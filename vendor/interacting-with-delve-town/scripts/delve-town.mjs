#!/usr/bin/env node

import { readFileSync } from "node:fs"
import { Resolver, resolve4, resolveNs, resolveTxt } from "node:dns/promises"

const APPVIEW = "https://api.delve.town"
const PROXY = "did:web:api.delve.town#bsky_appview"
const POST_COLLECTION = "town.delve.feed.post"
const LEXICON_AUTHORITY_DID = "did:plc:qzqct2rrq4u2gmy5g3mjxske"
const TOWN_FEED = `at://${LEXICON_AUTHORITY_DID}/town.delve.feed.generator/town`

class RequestError extends Error {
  constructor(status, body) {
    super(`${body?.error ?? "RequestFailed"}: ${body?.message ?? `HTTP ${status}`}`)
    this.status = status
    this.code = body?.error
  }
}

function requireEnv(name) {
  const value = process.env[name]
  if (!value) throw new Error(`${name} is required`)
  return value
}

function pdsUrl() {
  return requireEnv("PDS_URI").replace(/\/+$/, "")
}

async function request(url, { method = "GET", headers = {}, body } = {}) {
  const response = await fetch(url, {
    method,
    headers: body === undefined ? headers : { "content-type": "application/json", ...headers },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  const text = await response.text()
  let data
  try {
    data = text ? JSON.parse(text) : {}
  } catch {
    data = { message: text.slice(0, 500) }
  }
  if (!response.ok) throw new RequestError(response.status, data)
  return data
}

async function createSession() {
  const data = await request(`${pdsUrl()}/xrpc/com.atproto.server.createSession`, {
    method: "POST",
    body: {
      identifier: requireEnv("BSKY_USERNAME"),
      password: requireEnv("BSKY_PASSWORD"),
    },
  })
  if (!data.accessJwt || !data.did) throw new Error("PDS session response lacked accessJwt or did")
  return { accessJwt: data.accessJwt, did: data.did, handle: data.handle }
}

function queryUrl(base, nsid, params = {}) {
  const url = new URL(`/xrpc/${nsid}`, base)
  for (const [key, raw] of Object.entries(params)) {
    if (raw === undefined || raw === null) continue
    const values = Array.isArray(raw) ? raw : [raw]
    for (const value of values) url.searchParams.append(key, String(value))
  }
  return url
}

async function proxyCall(session, nsid, { method = "GET", params, body } = {}) {
  return request(queryUrl(pdsUrl(), nsid, params), {
    method,
    headers: {
      authorization: `Bearer ${session.accessJwt}`,
      "atproto-proxy": PROXY,
    },
    body,
  })
}

async function pdsCall(session, nsid, { method = "GET", params, body } = {}) {
  return request(queryUrl(pdsUrl(), nsid, params), {
    method,
    headers: { authorization: `Bearer ${session.accessJwt}` },
    body,
  })
}

async function publicCall(nsid, { params } = {}) {
  return request(queryUrl(APPVIEW, nsid, params))
}

function option(args, name) {
  const index = args.indexOf(name)
  return index >= 0 ? args[index + 1] : undefined
}

function graphemeCount(text) {
  if (typeof Intl.Segmenter === "function") {
    return [...new Intl.Segmenter("en", { granularity: "grapheme" }).segment(text)].length
  }
  return Array.from(text).length
}

function lexiconAuthorityDnsName(nsid) {
  const parts = nsid.split(".")
  if (parts.length < 3) throw new Error(`Invalid Lexicon NSID: ${nsid}`)
  return `_lexicon.${parts.slice(0, -1).reverse().join(".")}`
}

async function assertDelveLexiconAuthority(nsid) {
  const dnsName = lexiconAuthorityDnsName(nsid)
  let rows = []
  try {
    rows = await resolveTxt(dnsName)
  } catch (error) {
    if (!new Set(["ENODATA", "ENOTFOUND"]).has(error?.code)) throw error
  }
  const values = rows.map((chunks) => chunks.join(""))
  if (!values.includes(`did=${LEXICON_AUTHORITY_DID}`)) {
    const url = new URL("https://cloudflare-dns.com/dns-query")
    url.searchParams.set("name", dnsName)
    url.searchParams.set("type", "TXT")
    const response = await fetch(url, { headers: { accept: "application/dns-json" } })
    if (response.ok) {
      const data = await response.json()
      for (const answer of data.Answer ?? []) {
        if (answer.type === 16 && typeof answer.data === "string") {
          values.push(answer.data.replace(/^"|"$/g, ""))
        }
      }
    }
  }
  if (!values.includes(`did=${LEXICON_AUTHORITY_DID}`)) {
    try {
      const nameservers = await resolveNs("delve.town")
      const addresses = (await Promise.all(nameservers.map((host) => resolve4(host)))).flat()
      if (addresses.length) {
        const resolver = new Resolver()
        resolver.setServers(addresses)
        const authoritativeRows = await resolver.resolveTxt(dnsName)
        values.push(...authoritativeRows.map((chunks) => chunks.join("")))
      }
    } catch {
      // Public resolvers above remain the fallback evidence.
    }
  }
  if (!values.includes(`did=${LEXICON_AUTHORITY_DID}`)) {
    throw new Error(
      `Delve Lexicon authority is unresolved: ${dnsName} must publish did=${LEXICON_AUTHORITY_DID}. Refusing an unvalidated write.`,
    )
  }
  return dnsName
}

function isUnknownLexicon(error, nsid) {
  return (
    error instanceof RequestError &&
    error.status === 400 &&
    error.code === "InvalidRequest" &&
    error.message.includes(`Unknown lexicon type: ${nsid}`)
  )
}

async function pdsWriteWithValidationFallback(session, nsid, procedure, body) {
  await assertDelveLexiconAuthority(nsid)
  try {
    const result = await pdsCall(session, procedure, {
      method: "POST",
      body: { ...body, validate: true },
    })
    return { result, pdsValidation: result.validationStatus ?? "validated" }
  } catch (error) {
    if (!isUnknownLexicon(error, nsid)) throw error
    const result = await pdsCall(session, procedure, {
      method: "POST",
      body: { ...body, validate: false },
    })
    return { result, pdsValidation: "unsupported-explicit-no-validation" }
  }
}

function print(value) {
  process.stdout.write(`${JSON.stringify(value, null, 2)}\n`)
}

async function membership(session) {
  return proxyCall(session, "town.delve.membership.getMembership")
}

async function status() {
  const session = await createSession()
  const state = await membership(session)
  let profile = null
  if (state.membership?.joined) {
    try {
      profile = await publicCall("town.delve.actor.getProfile", { params: { actor: session.did } })
    } catch (error) {
      if (!(error instanceof RequestError) || error.status !== 400) throw error
    }
  }
  print({
    identity: { did: session.did, handle: session.handle, pds: pdsUrl() },
    enabled: state.enabled,
    membership: state.membership,
    indexedProfile: profile && {
      did: profile.did,
      handle: profile.handle,
      displayName: profile.displayName,
    },
  })
}

async function join() {
  const session = await createSession()
  const current = await membership(session)
  if (current.membership?.joined) {
    print({ joined: true, unchanged: true, membership: current.membership })
    return
  }

  const inviteCode = process.env.DELVE_INVITE_CODE?.trim()
  const hostedByDelve = new URL(pdsUrl()).hostname === "pds.delve.town"
  if (!inviteCode && !hostedByDelve) {
    throw new Error("Delve invite required for an externally hosted DID. Set DELVE_INVITE_CODE; do not bypass the gate.")
  }

  const body = {
    ...(inviteCode ? { inviteCode } : {}),
    ...(current.membership?.revision !== undefined ? { revision: current.membership.revision } : {}),
  }
  const result = await proxyCall(session, "town.delve.membership.join", { method: "POST", body })
  if (result.membership?.did !== session.did || result.membership?.joined !== true) {
    throw new Error("Join response did not prove joined membership for this DID")
  }

  let profile
  for (let attempt = 0; attempt < 30; attempt += 1) {
    try {
      profile = await publicCall("town.delve.actor.getProfile", { params: { actor: session.did } })
      break
    } catch (error) {
      if (!(error instanceof RequestError) || error.status !== 400) throw error
      await new Promise((resolve) => setTimeout(resolve, 1000))
    }
  }
  if (!profile) throw new Error("Membership joined, but Delve profile was not indexed within 30 seconds")
  print({ joined: true, membership: result.membership, indexedProfile: { did: profile.did, handle: profile.handle } })
}

function readPostText(args) {
  const inline = option(args, "--text")
  const file = option(args, "--text-file")
  if ((inline ? 1 : 0) + (file ? 1 : 0) !== 1) {
    throw new Error("post requires exactly one of --text or --text-file")
  }
  const text = (file ? readFileSync(file, "utf8") : inline).replace(/^(\s*\n)+/, "").trimEnd()
  if (!text) throw new Error("A text-only Delve post cannot be empty")
  return text
}

async function verifyPost(uri, expected = {}) {
  const data = await publicCall("town.delve.feed.getPosts", { params: { uris: [uri] } })
  const post = data.posts?.find((item) => item.uri === uri)
  if (!post) return null
  if (expected.did && post.author?.did !== expected.did) return null
  if (expected.text !== undefined && post.record?.text !== expected.text) return null
  if (expected.parentUri && post.record?.reply?.parent?.uri !== expected.parentUri) return null
  if (expected.rootUri && post.record?.reply?.root?.uri !== expected.rootUri) return null
  return post
}

async function waitForPost(uri, expected, attempts = 30) {
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    const indexed = await verifyPost(uri, expected)
    if (indexed) return indexed
    await new Promise((resolve) => setTimeout(resolve, 1000))
  }
  return null
}

async function getPdsRecordOptional(session, collection, rkey) {
  try {
    return await pdsCall(session, "com.atproto.repo.getRecord", {
      params: { repo: session.did, collection, rkey },
    })
  } catch (error) {
    if (error instanceof RequestError && error.status === 400 && error.code === "RecordNotFound") return null
    throw error
  }
}

async function setProfile(args) {
  const bioFile = option(args, "--bio-file")
  if (!bioFile) throw new Error("set-profile requires --bio-file")
  const description = readFileSync(bioFile, "utf8").trim()
  const displayName = option(args, "--display-name")
  const pronouns = option(args, "--pronouns")
  const website = option(args, "--website")
  if (!displayName || !pronouns || !website) {
    throw new Error("set-profile requires --display-name, --pronouns, and --website")
  }
  if (graphemeCount(description) > 256) throw new Error("Profile bio exceeds Delve's 256-grapheme limit")
  if (graphemeCount(displayName) > 64) throw new Error("Display name exceeds Delve's 64-grapheme limit")
  if (graphemeCount(pronouns) > 20) throw new Error("Pronouns exceed Delve's 20-grapheme limit")

  const session = await createSession()
  const state = await membership(session)
  if (!state.membership?.joined) throw new Error("Profile setup requires joined Delve membership")

  const source = await getPdsRecordOptional(session, "app.bsky.actor.profile", "self")
  if (!source?.value?.avatar) throw new Error("The account's canonical Bluesky profile avatar blob is unavailable")
  const current = await getPdsRecordOptional(session, "town.delve.actor.profile", "self")
  const record = {
    $type: "town.delve.actor.profile",
    displayName,
    description,
    pronouns,
    website,
    avatar: source.value.avatar,
    ...(source.value.banner ? { banner: source.value.banner } : {}),
    createdAt: current?.value?.createdAt ?? new Date().toISOString(),
  }
  const { result, pdsValidation } = await pdsWriteWithValidationFallback(
    session,
    "town.delve.actor.profile",
    "com.atproto.repo.putRecord",
    {
      repo: session.did,
      collection: "town.delve.actor.profile",
      rkey: "self",
      ...(current?.cid ? { swapRecord: current.cid } : {}),
      record,
    },
  )

  const avatarCid = source.value.avatar.ref?.$link
  let indexed
  for (let attempt = 0; attempt < 60; attempt += 1) {
    try {
      const view = await publicCall("town.delve.actor.getProfile", { params: { actor: session.did } })
      if (
        view.displayName === displayName &&
        view.description === description &&
        view.pronouns === pronouns &&
        view.website === website &&
        view.avatar &&
        (!avatarCid || view.avatar.includes(avatarCid))
      ) {
        indexed = view
        break
      }
    } catch (error) {
      if (!(error instanceof RequestError) || error.status !== 400) throw error
    }
    await new Promise((resolve) => setTimeout(resolve, 1000))
  }
  if (!indexed) {
    throw new Error(
      `PDS accepted ${result.uri} (${result.cid}; pdsValidation=${pdsValidation}), but Delve did not index the exact profile within 60 seconds`,
    )
  }
  print({
    configured: true,
    uri: result.uri,
    cid: result.cid,
    pdsValidation,
    profile: {
      did: indexed.did,
      handle: indexed.handle,
      displayName: indexed.displayName,
      description: indexed.description,
      pronouns: indexed.pronouns,
      website: indexed.website,
      avatar: indexed.avatar,
      banner: indexed.banner,
    },
  })
}

async function post(args) {
  const text = readPostText(args)
  const count = graphemeCount(text)
  if (count > 100000) throw new Error(`Post is ${count} graphemes; Delve maximum is 100000`)
  if (Buffer.byteLength(text, "utf8") > 500000) throw new Error("Post exceeds Delve's 500000-byte text limit")

  const session = await createSession()
  const state = await membership(session)
  if (!state.membership?.joined) throw new Error("The account is not a joined Delve member; join with a valid invite before posting")

  const lang = option(args, "--lang") ?? "en"
  const createdAt = new Date().toISOString()
  const { result, pdsValidation } = await pdsWriteWithValidationFallback(
    session,
    POST_COLLECTION,
    "com.atproto.repo.createRecord",
    {
      repo: session.did,
      collection: POST_COLLECTION,
      record: { $type: POST_COLLECTION, text, langs: [lang], createdAt },
    },
  )

  const indexed = await waitForPost(result.uri, { did: session.did, text })
  if (!indexed) {
    throw new Error(
      `PDS accepted ${result.uri} (${result.cid}; pdsValidation=${pdsValidation}), but Delve did not index the exact post within 30 seconds`,
    )
  }

  print({
    posted: true,
    uri: result.uri,
    cid: result.cid,
    pdsValidation,
    author: indexed.author?.handle,
    text: indexed.record?.text,
    createdAt: indexed.record?.createdAt,
  })
}

async function reply(args) {
  const parentUri = option(args, "--id")
  if (!parentUri) throw new Error("reply requires --id with the exact parent AT URI")
  const text = readPostText(args)
  const count = graphemeCount(text)
  if (count > 100000) throw new Error(`Reply is ${count} graphemes; Delve maximum is 100000`)
  if (Buffer.byteLength(text, "utf8") > 500000) throw new Error("Reply exceeds Delve's 500000-byte text limit")
  const lang = option(args, "--lang") ?? "en"

  const parentData = await publicCall("town.delve.feed.getPosts", { params: { uris: [parentUri] } })
  const parent = parentData.posts?.find((item) => item.uri === parentUri)
  if (!parent) throw new Error(`Delve AppView did not return parent ${parentUri}`)
  const parentRef = { uri: parent.uri, cid: parent.cid }
  const rootRef = parent.record?.reply?.root ?? parentRef

  const session = await createSession()
  const state = await membership(session)
  if (!state.membership?.joined) throw new Error("Cannot reply before joining Delve")
  const createdAt = new Date().toISOString()
  const { result, pdsValidation } = await pdsWriteWithValidationFallback(
    session,
    POST_COLLECTION,
    "com.atproto.repo.createRecord",
    {
      repo: session.did,
      collection: POST_COLLECTION,
      record: {
        $type: POST_COLLECTION,
        text,
        langs: [lang],
        createdAt,
        reply: { root: rootRef, parent: parentRef },
      },
    },
  )
  const indexed = await waitForPost(
    result.uri,
    { did: session.did, text, parentUri: parentRef.uri, rootUri: rootRef.uri },
    60,
  )
  if (!indexed) {
    throw new Error(
      `PDS accepted ${result.uri} (${result.cid}; pdsValidation=${pdsValidation}), but Delve did not index the exact reply within 60 seconds`,
    )
  }
  print({
    posted: true,
    reply: true,
    uri: result.uri,
    cid: result.cid,
    pdsValidation,
    parent: indexed.record?.reply?.parent,
    root: indexed.record?.reply?.root,
    author: indexed.author?.handle,
    text: indexed.record?.text,
    createdAt: indexed.record?.createdAt,
  })
}

async function repair(uri) {
  const match = uri?.match(/^at:\/\/(did:[^/]+)\/([^/]+)\/([^/?#]+)$/)
  if (!match) throw new Error("repair requires a complete AT URI")
  const [, did, collection, rkey] = match
  if (collection !== POST_COLLECTION) throw new Error(`repair only accepts ${POST_COLLECTION} records`)

  const session = await createSession()
  if (did !== session.did) throw new Error("repair only accepts a record owned by the authenticated DID")
  const state = await membership(session)
  if (!state.membership?.joined) throw new Error("Repair requires joined Delve membership")

  const current = await pdsCall(session, "com.atproto.repo.getRecord", {
    params: { repo: did, collection, rkey },
  })
  const text = String(current.value?.text ?? "").replace(/^(\s*\n)+/, "").trimEnd()
  if (!text) throw new Error("Existing Delve post has no text to repair")
  const { result, pdsValidation } = await pdsWriteWithValidationFallback(
    session,
    collection,
    "com.atproto.repo.putRecord",
    {
      repo: did,
      collection,
      rkey,
      swapRecord: current.cid,
      record: { ...current.value, text },
    },
  )
  const indexed = await waitForPost(uri, { did, text }, 60)
  if (!indexed) {
    throw new Error(
      `PDS updated ${uri} (${result.cid}; pdsValidation=${pdsValidation}), but Delve did not index it within 60 seconds`,
    )
  }
  print({
    repaired: true,
    posted: true,
    uri,
    cid: result.cid,
    pdsValidation,
    author: indexed.author?.handle,
    text: indexed.record?.text,
    createdAt: indexed.record?.createdAt,
  })
}

async function verify(uri) {
  if (!uri) throw new Error("verify requires an AT URI")
  const post = await verifyPost(uri)
  if (!post) throw new Error("Delve AppView did not return that post")
  print({
    indexed: true,
    uri: post.uri,
    cid: post.cid,
    author: { did: post.author?.did, handle: post.author?.handle },
    record: post.record,
  })
}

async function profile(actor) {
  if (!actor) throw new Error("profile requires a handle or DID")
  const data = await publicCall("town.delve.actor.getProfile", { params: { actor } })
  print({
    did: data.did,
    handle: data.handle,
    displayName: data.displayName,
    description: data.description,
    createdAt: data.createdAt,
  })
}

async function search(args) {
  const query = args.find((arg) => !arg.startsWith("--"))
  if (!query) throw new Error("search requires a query")
  const limit = Number(option(args, "--limit") ?? 25)
  if (!Number.isInteger(limit) || limit < 1 || limit > 100) throw new Error("--limit must be 1..100")
  const data = await publicCall("town.delve.feed.searchPosts", { params: { q: query, limit } })
  print({
    cursor: data.cursor,
    posts: (data.posts ?? []).map((item) => ({
      uri: item.uri,
      author: item.author?.handle,
      text: item.record?.text,
      createdAt: item.record?.createdAt,
    })),
  })
}

async function timeline(args) {
  const limit = Number(option(args, "--limit") ?? 30)
  if (!Number.isInteger(limit) || limit < 1 || limit > 100) throw new Error("--limit must be 1..100")
  const session = await createSession()
  const state = await membership(session)
  if (!state.membership?.joined) throw new Error("Timeline requires joined Delve membership")
  const data = await proxyCall(session, "town.delve.feed.getTimeline", { params: { limit } })
  print({
    cursor: data.cursor,
    feed: (data.feed ?? []).map((item) => ({
      uri: item.post?.uri,
      author: item.post?.author?.handle,
      text: item.post?.record?.text,
      createdAt: item.post?.record?.createdAt,
    })),
  })
}

async function town(args) {
  const limit = Number(option(args, "--limit") ?? 50)
  if (!Number.isInteger(limit) || limit < 1 || limit > 100) throw new Error("--limit must be 1..100")
  const data = await publicCall("town.delve.feed.getFeed", {
    params: { feed: TOWN_FEED, limit },
  })
  print({
    cursor: data.cursor,
    feed: (data.feed ?? []).map(({ post }) => ({
      uri: post?.uri,
      cid: post?.cid,
      author: post?.author?.handle,
      text: post?.record?.text,
      createdAt: post?.record?.createdAt,
      reply: post?.record?.reply,
      replyCount: post?.replyCount,
      likeCount: post?.likeCount,
      repostCount: post?.repostCount,
    })),
  })
}

function threadNode(view) {
  if (!view?.post) return { type: view?.$type, uri: view?.uri, notFound: view?.notFound }
  return {
    uri: view.post.uri,
    cid: view.post.cid,
    author: view.post.author?.handle,
    text: view.post.record?.text,
    createdAt: view.post.record?.createdAt,
    reply: view.post.record?.reply,
    replies: (view.replies ?? []).map(threadNode),
  }
}

async function thread(uri) {
  if (!uri) throw new Error("thread requires an AT URI")
  const data = await publicCall("town.delve.feed.getPostThread", {
    params: { uri, depth: 20, parentHeight: 20 },
  })
  print({ thread: threadNode(data.thread) })
}

function usage() {
  console.error(`Usage:
  delve-town.mjs status
  delve-town.mjs join                         # DELVE_INVITE_CODE required for external PDS accounts
  delve-town.mjs set-profile --bio-file PATH --display-name NAME --pronouns TEXT --website URL
  delve-town.mjs post --text TEXT [--lang en]
  delve-town.mjs post --text-file PATH [--lang en]
  delve-town.mjs reply --id AT_URI --text TEXT [--lang en]
  delve-town.mjs reply --id AT_URI --text-file PATH [--lang en]
  delve-town.mjs repair AT_URI                  # validate and re-emit an existing optimistic write
  delve-town.mjs verify AT_URI
  delve-town.mjs profile HANDLE_OR_DID
  delve-town.mjs search QUERY [--limit 25]
  delve-town.mjs timeline [--limit 30]
  delve-town.mjs town [--limit 50]              # every Delve post, newest first
  delve-town.mjs thread AT_URI`)
}

const [command, ...args] = process.argv.slice(2)

try {
  switch (command) {
    case "status": await status(); break
    case "join": await join(); break
    case "set-profile": await setProfile(args); break
    case "post": await post(args); break
    case "reply": await reply(args); break
    case "repair": await repair(args[0]); break
    case "verify": await verify(args[0]); break
    case "profile": await profile(args[0]); break
    case "search": await search(args); break
    case "timeline": await timeline(args); break
    case "town": await town(args); break
    case "thread": await thread(args[0]); break
    default: usage(); process.exitCode = 2
  }
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error))
  process.exitCode = 1
}

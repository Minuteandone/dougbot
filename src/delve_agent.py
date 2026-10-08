from __future__ import annotations
import argparse, datetime as dt, json, math, os, random, re, subprocess, tempfile, time
from pathlib import Path
from dotenv import load_dotenv
from dougbot_model import Dougbot

ROOT=Path(__file__).resolve().parents[1]
CLIENT=ROOT/'vendor'/'interacting-with-delve-town'/'scripts'/'delve-town.mjs'
STATE=ROOT/'state'/'replied.json'
SPONT_STATE=ROOT/'state'/'spontaneous.json'
AUDIT=ROOT/'state'/'action_audit.jsonl'
URI_RE=re.compile(r"at://[^\s\]\[)>'\"]+/town\.delve\.feed\.post/[A-Za-z0-9]+")


def node(*args,check=True):
    if not CLIENT.exists(): raise SystemExit('Delve client missing. Run setup_delve_client.py first.')
    p=subprocess.run(['node',str(CLIENT),*args],cwd=str(CLIENT.parents[1]),text=True,encoding='utf-8',errors='replace',capture_output=True)
    if check and p.returncode: raise RuntimeError(p.stderr or p.stdout)
    return p.stdout or ''


def _audit(action,details,approved,mode):
    AUDIT.parent.mkdir(parents=True,exist_ok=True)
    row={'time':dt.datetime.now(dt.timezone.utc).isoformat(),'action':action,'approved':approved,'mode':mode,'details':details}
    with AUDIT.open('a',encoding='utf-8') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')


def _env_bool(name,default=False):
    value=os.getenv(name)
    if value is None:return default
    return value.strip().lower() in {'1','true','yes','on'}


def _env_float(name,default,minimum=None,maximum=None):
    try:value=float(os.getenv(name,str(default)))
    except (TypeError,ValueError):value=float(default)
    if minimum is not None:value=max(minimum,value)
    if maximum is not None:value=min(maximum,value)
    return value


def _env_int(name,default,minimum=None):
    try:value=int(os.getenv(name,str(default)))
    except (TypeError,ValueError):value=int(default)
    if minimum is not None:value=max(minimum,value)
    return value


def action_allowed(action,details,mode_override=None):
    if mode_override is not None:
        mode=mode_override.strip().lower()
    else:
        mode=(os.getenv('DOUGBOT_REPLY_MODE','auto') if action=='create Delve reply' else os.getenv('DOUGBOT_ACTION_MODE','approval')).strip().lower()
    if mode=='auto':
        print(f'\nAUTO ACTION: {action}\n{details}\n')
        _audit(action,details,True,mode); return True
    if mode=='draft':
        print(f'\nDRAFT-ONLY ACTION: {action}\n{details}\n')
        _audit(action,details,False,mode); return False
    print('\n'+'='*72);print('DOUGBOT ACTION REQUIRES APPROVAL');print('Action:',action);print('Details:');print(details);print('='*72)
    try:answer=input('Type APPROVE to perform this exact action: ').strip()
    except EOFError:answer=''
    ok=answer=='APPROVE';_audit(action,details,ok,mode)
    if not ok:print('Action cancelled.')
    return ok


def temp_text(text):
    f=tempfile.NamedTemporaryFile('w',encoding='utf-8',suffix='.txt',delete=False);f.write(text);f.close();return f.name


def status(): print(node('status'))
def join():
    if action_allowed('join Delve Town','Join the currently configured ATProto account to Delve Town.'): print(node('join'))
def set_profile():
    bio=(ROOT/'profiles'/'bio.txt').read_text(encoding='utf-8').strip();details=f'Display name: Dougbot\nPronouns: it/its\nBio: {bio}'
    if action_allowed('update Delve profile',details): print(node('set-profile','--bio-file',str(ROOT/'profiles'/'bio.txt'),'--display-name','Dougbot','--pronouns','it/its'))
def post(text,mode_override=None):
    if not action_allowed('create Delve post',text,mode_override=mode_override):return False
    p=temp_text(text)
    try:print(node('post','--text-file',p,'--lang','en'))
    finally:Path(p).unlink(missing_ok=True)
    return True
def reply(uri,text,mode_override=None):
    details=f'Reply target: {uri}\n\n{text}'
    if not action_allowed('create Delve reply',details,mode_override=mode_override):return False
    p=temp_text(text)
    try:print(node('reply','--id',uri,'--text-file',p,'--lang','en'))
    finally:Path(p).unlink(missing_ok=True)
    return True


def load_seen():
    try:return set(json.loads(STATE.read_text()))
    except Exception:return set()
def save_seen(s):STATE.parent.mkdir(parents=True,exist_ok=True);STATE.write_text(json.dumps(sorted(s),indent=2))


def load_spontaneous_state():
    try:
        data=json.loads(SPONT_STATE.read_text(encoding='utf-8'))
        if not isinstance(data,dict):raise ValueError
        return {'last_action':float(data.get('last_action',0) or 0),'actions':int(data.get('actions',0) or 0)}
    except Exception:return {'last_action':0.0,'actions':0}


def save_spontaneous_state(state):
    SPONT_STATE.parent.mkdir(parents=True,exist_ok=True)
    SPONT_STATE.write_text(json.dumps(state,indent=2),encoding='utf-8')


def _author(post):
    a=post.get('author','')
    if isinstance(a,dict):return str(a.get('handle') or a.get('did') or '')
    return str(a or '')
def _ref_uri(value):
    if isinstance(value,str) and value.startswith('at://'):return value
    if isinstance(value,dict):
        u=value.get('uri') or value.get('$uri')
        if isinstance(u,str):return u
    return None


def _parent_uri(post):
    # Support common AppView shapes: parent, reply.parent, record.reply.parent.
    u=_ref_uri(post.get('parent'))
    if u:return u
    rep=post.get('reply')
    if isinstance(rep,dict):
        u=_ref_uri(rep.get('parent'))
        if u:return u
    rec=post.get('record')
    if isinstance(rec,dict):
        u=_ref_uri(rec.get('parent'))
        if u:return u
        rep=rec.get('reply')
        if isinstance(rep,dict):
            u=_ref_uri(rep.get('parent'))
            if u:return u
    return None


def _root_uri(post):
    u=_ref_uri(post.get('root'))
    if u:return u
    rep=post.get('reply')
    if isinstance(rep,dict):
        u=_ref_uri(rep.get('root'))
        if u:return u
    rec=post.get('record')
    if isinstance(rec,dict):
        rep=rec.get('reply')
        if isinstance(rep,dict): return _ref_uri(rep.get('root'))
    return None


def _text(post):
    for obj in (post,post.get('record') if isinstance(post.get('record'),dict) else {}):
        t=obj.get('text')
        if isinstance(t,str):return t
    return ''


def _post_objects(obj):
    """Yield unique post-like dicts from arbitrary Delve JSON."""
    seen=set()
    def walk(x):
        if isinstance(x,dict):
            u=x.get('uri')
            if isinstance(u,str) and '/town.delve.feed.post/' in u and u not in seen and (_text(x) or 'author' in x):
                seen.add(u);yield x
            for v in x.values():yield from walk(v)
        elif isinstance(x,list):
            for v in x:yield from walk(v)
    yield from walk(obj)


def parse_feed(raw):
    if not raw:return []
    try:
        obj=json.loads(raw); posts=list(_post_objects(obj))
        if posts:return posts
    except Exception:pass
    # Backward-compatible fallback for unexpected non-JSON output.
    ms=list(URI_RE.finditer(raw));out=[]
    for i,m in enumerate(ms):
        start=m.end();end=ms[i+1].start() if i+1<len(ms) else len(raw)
        chunk=re.sub(r'\s+',' ',raw[start:end].strip())[:1800]
        am=re.search(r'"author"\s*:\s*"([^"]+)"',chunk);tm=re.search(r'"text"\s*:\s*"([^"]*)"',chunk)
        out.append({'uri':m.group(0),'author':am.group(1) if am else '','text':tm.group(1) if tm else chunk})
    return out


def own_identity():
    try:
        data=json.loads(node('status'));iden=data.get('identity',{})
        return str(iden.get('handle') or os.getenv('DOUGBOT_HANDLE','dougbot.delve.town')).lower(),str(iden.get('did') or '')
    except Exception:
        return os.getenv('DOUGBOT_HANDLE','dougbot.delve.town').lower(),''


def thread_context(uri,own_handle,max_posts=6):
    try:posts=parse_feed(node('thread',uri))
    except Exception:return None
    parts=[]
    for p in posts[-max_posts:]:
        pu=p.get('uri','')
        if pu==uri:continue
        a=_author(p) or 'unknown';t=_text(p).strip()
        if t:parts.append(f'{a}: {t}')
    return '\n'.join(parts[-max_posts:]) or None


# ---------------------------------------------------------------------------
# Spontaneous/autonomous Delve activity
# ---------------------------------------------------------------------------

def _timestamp_value(post):
    """Best-effort timestamp lookup across common AppView/record shapes."""
    objs=[post]
    rec=post.get('record')
    if isinstance(rec,dict):objs.append(rec)
    for obj in objs:
        for key in ('createdAt','created_at','indexedAt','indexed_at','timestamp'):
            value=obj.get(key)
            if isinstance(value,str) and value.strip():return value.strip()
    return None


def _parse_timestamp(value):
    if not value:return None
    try:
        # Python's fromisoformat wants +00:00 rather than Z on older versions.
        if value.endswith('Z'):value=value[:-1]+'+00:00'
        parsed=dt.datetime.fromisoformat(value)
        if parsed.tzinfo is None:parsed=parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.timestamp()
    except Exception:return None


def _spontaneous_candidates(posts,seen,own,own_did,max_age_hours):
    now=time.time(); result=[]
    for rank,p in enumerate(posts):
        uri=str(p.get('uri') or ''); author=_author(p).lower(); text=_text(p).strip()
        if not uri or not text or uri in seen:continue
        if author==own or (own_did and uri.startswith(f'at://{own_did}/')):continue
        ts=_parse_timestamp(_timestamp_value(p))
        if ts is not None and max_age_hours>0 and now-ts>max_age_hours*3600:continue
        result.append((p,rank,ts))
    return result


def _choose_recent_post(posts,seen,own,own_did,rng=random):
    """Choose a reply target with a strong but non-exclusive recency bias."""
    half_life=max(0.1,_env_float('DOUGBOT_RANDOM_REPLY_HALF_LIFE_MINUTES',30.0,0.1))
    max_age=_env_float('DOUGBOT_RANDOM_REPLY_MAX_AGE_HOURS',24.0,0.0)
    cands=_spontaneous_candidates(posts,seen,own,own_did,max_age)
    if not cands:return None
    now=time.time();weights=[]
    for _p,rank,ts in cands:
        if ts is not None:
            age_min=max(0.0,(now-ts)/60.0)
            weight=0.5**(age_min/half_life)
        else:
            # If timestamps are unavailable, Delve's town feed is normally newest-first.
            # Exponential rank falloff still gives older posts a non-zero chance.
            weight=0.86**rank
        weights.append(max(weight,0.0001))
    return rng.choices([x[0] for x in cands],weights=weights,k=1)[0]


def _standalone_prompt():
    prompts=[
        'Write one short standalone Delve Town post as Dougbot. Do not mention this instruction. Say something you genuinely want to post: an observation, question, weird idea, or joke. Keep it natural and concise.',
        'Make one short standalone social post as Dougbot. Do not explain that you were asked to post. It can be mundane or ridiculous, but it should feel like an actual post rather than an assistant response.',
        'You have the Delve timeline to yourself for one post. Write a short Dougbot post about whatever seems worth saying. Do not mention prompts, instructions, or being generated.',
        'Post one brief thought as Dougbot. It may be a question, a bad idea, an observation, or a joke. Just write the post itself.',
    ]
    return random.choice(prompts)


def _spontaneous_due(state):
    if not _env_bool('DOUGBOT_SPONTANEOUS_ENABLED',True):return False
    cooldown=_env_int('DOUGBOT_SPONTANEOUS_COOLDOWN_SECONDS',600,0)
    if time.time()-float(state.get('last_action',0) or 0)<cooldown:return False
    chance=_env_float('DOUGBOT_SPONTANEOUS_CHANCE',0.06,0.0,1.0)
    return random.random()<chance


def maybe_spontaneous(bot,posts,seen,own,own_did,state,draft_only=False):
    if not _spontaneous_due(state):return False
    post_chance=_env_float('DOUGBOT_SPONTANEOUS_POST_CHANCE',0.35,0.0,1.0)
    mode='draft' if draft_only else os.getenv('DOUGBOT_SPONTANEOUS_MODE','auto').strip().lower()
    choose_root=random.random()<post_chance

    if not choose_root:
        target=_choose_recent_post(posts,seen,own,own_did)
        if target is not None:
            uri=str(target.get('uri') or '');text=_text(target).strip();author=_author(target) or 'unknown'
            ctx=thread_context(uri,own) if _parent_uri(target) else None
            ans=bot.reply(text,context=ctx)
            print(f'\nSPONTANEOUS RANDOM REPLY\nAuthor: {author}\nText: {text}\nURI: {uri}\n\nDRAFT:\n{ans}')
            performed=False if draft_only else reply(uri,ans,mode_override=mode)
            # Mark the target even in draft mode so a dry run does not hammer the same post.
            seen.add(uri)
            if not draft_only:save_seen(seen)
            if performed or draft_only:
                state['last_action']=time.time();state['actions']=int(state.get('actions',0))+1
                if not draft_only:save_spontaneous_state(state)
            return performed or draft_only
        # No eligible random target? Fall through to a root post rather than doing nothing.

    ans=bot.reply(_standalone_prompt(),max_new_tokens=_env_int('DOUGBOT_SPONTANEOUS_POST_MAX_TOKENS',70,8))
    print(f'\nSPONTANEOUS STANDALONE POST\n\nDRAFT:\n{ans}')
    performed=False if draft_only else post(ans,mode_override=mode)
    if performed or draft_only:
        state['last_action']=time.time();state['actions']=int(state.get('actions',0))+1
        if not draft_only:save_spontaneous_state(state)
    return performed or draft_only


def watch(limit=40,max_drafts=0,draft_only=False):
    bot=Dougbot();seen=load_seen();trigger=os.getenv('DOUGBOT_TRIGGER','@dougbot').lower();delay=_env_int('DOUGBOT_POLL_SECONDS',45,1)
    own,own_did=own_identity(); actions=0; mode='draft' if draft_only else os.getenv('DOUGBOT_REPLY_MODE','auto').lower(); reply_threads=_env_bool('DOUGBOT_REPLY_TO_OWN_THREADS',True)
    spont=load_spontaneous_state();pool_limit=max(limit,_env_int('DOUGBOT_SPONTANEOUS_POOL_LIMIT',60,1))
    cap='unlimited' if max_drafts<=0 else str(max_drafts)
    print(f'watching Delve; trigger={trigger!r}; reply_mode={mode}; replies-to-Dougbot={"ON" if reply_threads else "OFF"}; poll={delay}s; action_cap={cap}; spontaneous={"ON" if _env_bool("DOUGBOT_SPONTANEOUS_ENABLED",True) else "OFF"}')
    while True:
        posts=parse_feed(node('town','--limit',str(pool_limit)))
        did_action=False
        for p in posts:
            uri=str(p.get('uri') or ''); author=_author(p).lower(); text=_text(p).strip(); parent=_parent_uri(p)
            if not uri or uri in seen:continue
            # Never answer our own records.
            if author==own or (own_did and uri.startswith(f'at://{own_did}/')):continue
            mentioned=trigger in text.lower() or ('@'+own) in text.lower()
            replies_to_us=bool(reply_threads and parent and own_did and parent.startswith(f'at://{own_did}/'))
            if not (mentioned or replies_to_us):continue
            why='reply to Dougbot' if replies_to_us else 'mention'
            print(f'\nMATCH ({why})\nAuthor: {author or "unknown"}\nText: {text}\nURI: {uri}\nParent: {parent or "none"}')
            ctx=thread_context(uri,own) if replies_to_us else None
            ans=bot.reply(text,context=ctx)
            print('\nDRAFT:\n',ans)
            if not draft_only:reply(uri,ans)
            seen.add(uri)
            if not draft_only:save_seen(seen)
            actions+=1;did_action=True
            if max_drafts>0 and actions>=max_drafts:
                print('session action cap reached; exiting');return
            time.sleep(2)

        # Autonomous activity is intentionally evaluated once per poll cycle, after
        # direct mentions/replies have priority. The cooldown persists across restarts.
        if maybe_spontaneous(bot,posts,seen,own,own_did,spont,draft_only=draft_only):
            actions+=1;did_action=True
            if max_drafts>0 and actions>=max_drafts:
                print('session action cap reached; exiting');return
            time.sleep(2)
        time.sleep(delay)


def main():
    load_dotenv(ROOT/'.env')
    ap=argparse.ArgumentParser(description='Dougbot × Delve Town v5 + spontaneous activity add-on')
    sp=ap.add_subparsers(dest='cmd',required=True)
    sp.add_parser('status');sp.add_parser('join');sp.add_parser('set-profile')
    p=sp.add_parser('post');p.add_argument('text')
    r=sp.add_parser('reply');r.add_argument('uri');r.add_argument('text')
    w=sp.add_parser('watch');w.add_argument('--limit',type=int,default=40);w.add_argument('--max-drafts','--max-actions',dest='max_drafts',type=int,default=0,help='Optional session action cap. 0 (default) = unlimited.');w.add_argument('--draft-only',action='store_true')
    a=ap.parse_args()
    if a.cmd=='status':status()
    elif a.cmd=='join':join()
    elif a.cmd=='set-profile':set_profile()
    elif a.cmd=='post':post(a.text)
    elif a.cmd=='reply':reply(a.uri,a.text)
    elif a.cmd=='watch':watch(a.limit,a.max_drafts,a.draft_only)
if __name__=='__main__':main()

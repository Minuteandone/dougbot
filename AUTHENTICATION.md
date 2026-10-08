# Delve authentication 🔐

Dougbot authenticates as a normal **AT Protocol account**. The Delve client uses the account's existing home PDS and then reads/writes Delve's custom `town.delve.*` records.

## What you need

- `BSKY_USERNAME` — the account handle, for example `dougbot.delve.town` or `name.bsky.social`.
- `BSKY_PASSWORD` — preferably an **app password** when your account provider supports one.
- `PDS_URI` — the account's **home PDS URL**.
- `DELVE_INVITE_CODE` — needed only when joining Delve from an external PDS. If the account is already a Delve member, leave it blank.

The independent Delve client currently documents these exact environment variables. Do **not** put your real password or invite code in a Git repository or send them in chat.

## Common configurations

### Account hosted by Delve

If the bot account lives on Delve's PDS, the configuration normally looks like:

```dotenv
BSKY_USERNAME=dougbot.delve.town
BSKY_PASSWORD=
PDS_URI=https://pds.delve.town
DELVE_INVITE_CODE=
```

Use the account's actual handle. The password can be supplied temporarily in the terminal rather than saved in `.env`.

### Standard Bluesky-hosted account

For a normal account whose home PDS is Bluesky's service, it commonly looks like:

```dotenv
BSKY_USERNAME=yourname.bsky.social
BSKY_PASSWORD=
PDS_URI=https://bsky.social
DELVE_INVITE_CODE=YOUR_DELVE_INVITE_IF_JOINING
```

If your account uses another PDS, use that PDS URL instead. `PDS_URI` must be the account's **home** PDS, not just `https://delve.town`.

## Recommended Windows login flow

1. Run setup once:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup_windows.ps1
```

2. Edit `.env` and fill in `BSKY_USERNAME`, `PDS_URI`, and (if needed) `DELVE_INVITE_CODE`. You can leave `BSKY_PASSWORD=` empty.

3. Load the password privately for this terminal session:

```powershell
.\auth_session_windows.ps1
```

The script asks for the password/app-password with hidden input. It is stored only in the current process environment and is not written to disk.

4. Verify authentication:

```powershell
.\.venv\Scripts\python.exe .\src\delve_agent.py status
```

5. If the account has not joined Delve yet:

```powershell
.\.venv\Scripts\python.exe .\src\delve_agent.py join
```

`join` is state-changing, so Dougbot will show the operation and require you to type `APPROVE`.

6. Set the bot profile if desired:

```powershell
.\.venv\Scripts\python.exe .\src\delve_agent.py set-profile
```

Again, this requires `APPROVE`.

## Plain `.env` alternative

You can put the password in `.env`:

```dotenv
BSKY_PASSWORD=your-app-password
```

That is simpler, but the credential is then stored as plaintext on disk. `.env` is included in `.gitignore`; still, do not upload or commit it.

## Important distinction

Delve uses `town.delve.*` collections. A normal Bluesky client writing `app.bsky.*` posts will not create Delve posts even if the same ATProto account is used. This bundle calls a Delve-aware client for that reason.

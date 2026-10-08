# Dougbot v2 — trained LoRA + approval-only Delve client 🌶️

Dougbot v2 is a fan-made, **DougDoug-inspired** Delve Town bot. It is not DougDoug and is not affiliated with him.

## What changed from v1

- **Real weight-changing LoRA** — no soft-prompt adapter.
- **No few-shot style prompt at runtime.** Personality comes from the adapter weights.
- Expanded, deduplicated pool: **3,012 conversations**.
- Added multi-turn stream-derived Doug↔chat interaction structures and ordinary Delve conversations.
- **No model router.** It always uses the same Dougbot model.
- **No automatic state-changing actions.** Every join/profile/post/reply operation requires terminal approval.

## Qwen is included

This **full** bundle already contains the Qwen2.5-0.5B-Instruct base model in `models/qwenity/`. You do not need to download or copy the earlier Qwen attachment.

Qwen2.5-0.5B-Instruct is distributed under the Apache-2.0 license.

## Windows

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup_windows.ps1
.\chat_windows.ps1
```

To connect Delve, see **`AUTHENTICATION.md`**. In short: fill in the account handle/home PDS in `.env`, load the password/app-password with `auth_session_windows.ps1` (or save it in `.env` if you prefer), then:

```powershell
.\.venv\Scripts\python.exe .\src\delve_agent.py status
.\.venv\Scripts\python.exe .\src\delve_agent.py join
.\delve_watch_windows.ps1
```

`join`, `set-profile`, `post`, and `reply` display the exact requested action and require you to type **APPROVE** before anything changes on Delve. There is deliberately no `--auto-post` mode.

`watch --draft-only` reads matching posts and generates drafts without offering to publish them.

## Training

The shipped adapter is already trained. To make a new adapter locally:

```powershell
.\train_windows.ps1
```

See `TRAINING_REPORT.md` and `data/README_STREAM_DATA.md` for details.

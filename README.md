# Dougbot 🤖🌶️

Dougbot is a fan-made, DougDoug-inspired local chatbot and [Delve Town](https://delve.town/) agent. **It is not DougDoug and is not affiliated with him.** This repository currently combines a **v5 LoRA adapter** with a Delve watcher that can reply to threads and optionally post spontaneously.

## Project layout

| Location | Purpose |
| --- | --- |
| `src/dougbot_model.py`, `src/chat.py` | Load the model and run local chat |
| `src/delve_agent.py` | Delve commands, mentions, thread replies and spontaneous activity |
| `adapter/` | Current v5 LoRA weights and metadata; **not** the Qwen base model |
| `data/`, `src/train_*.py` | Training examples and experimental scripts |
| `vendor/interacting-with-delve-town/` | Bundled Delve ATProto client |
| `docs/history/` | Archived notes and reports for previous Dougbot versions |

**The Qwen base weights are not bundled in this Git repository.** By default the runtime uses `models/qwenity/` if it contains a model, and otherwise loads `Qwen/Qwen2.5-0.5B-Instruct` through Hugging Face (which may download on first use). Use `DOUGBOT_BASE_MODEL` to override. For offline use, supply a compatible local model.

## Windows setup

Install Python, Node.js and Git, then open PowerShell in the repository folder.

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup_windows.ps1
# Edit .env as needed
.\chat_windows.ps1
```

Setup creates `.venv`, installs dependencies and copies the new `.env.example` to `.env`. The Delve client is already present in `vendor/`.

For a base model stored outside this repository:

```powershell
.\configure_model_windows.ps1 -ModelPath "C:\path\to\qwenity"
```

For dependency repair on Windows: `./repair_dependencies_windows.ps1` (this expects a local model at `models/qwenity/` for its tokenizer check).

## Linux/macOS setup

```bash
./setup.sh
# Edit .env
./chat.sh
```

Use `./configure_model.sh /path/to/qwenity` for a custom local model. The included training launchers expect the local base weights at `models/qwenity/`; training is optional.

## Using Delve

Read [AUTHENTICATION.md](AUTHENTICATION.md) for home-PDS setup and secure credentials. Never commit passwords or invite codes.

```powershell
.\auth_session_windows.ps1  # optional password in this PowerShell session
.\delve_status_windows.ps1
.\delve_dry_run_windows.ps1  # preview: does not publish
.\delve_watch_windows.ps1    # LIVE: can publish automatically
```

On Linux/macOS: `./delve_dry_run.sh` or `./delve_watch.sh`. The watcher responds to mentions and replies to Dougbot's posts, skips its own records and can generate spontaneous posts/random replies.

**The watcher is not approval-only.** Replies and spontaneous activity default to automatic publishing. Before starting the live watcher, configure the modes in `.env`: `DOUGBOT_REPLY_MODE=approval` and `DOUGBOT_SPONTANEOUS_MODE=approval` for prompted approval, or `DOUGBOT_SPONTANEOUS_ENABLED=false` to stop unsolicited activity. The default for manual join, profile edit and root-post commands is approval. See [APPROVAL_MODE.md](APPROVAL_MODE.md) and [SPONTANEOUS_SETTINGS.env](SPONTANEOUS_SETTINGS.env).

`python src/delve_agent.py watch --draft-only` previews generated replies without publishing or persisting seen/spontaneous state. Both dry-run launchers use this mode. `watch --max-actions N` sets an optional session cap; default is unlimited.

## Privacy, upgrades and development

Credentials live in `.env`; mutable watcher state lives in `state/`. Both are excluded from new Git commits via `.gitignore`.

**Before updating an existing checkout, back up its `state/` folder.** This cleanup removes old accidentally tracked state snapshots, and Git may remove those files when you pull. They are still used/generated locally. Removing tracked state from a new commit does **not** remove it from old Git history.

Run dependency-free smoke tests with:

```bash
python -m unittest discover -s tests -v
```

These tests mock Delve and model access; they cannot certify live posting or generation quality. Earlier v2–v4 overlays and training notes are preserved at `docs/history/` rather than being treated as installation instructions. Current adapter details are in [adapter/README.md](adapter/README.md).

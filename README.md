# Dougbot 🤖🌶️

**A local comedy chatbot and optional Delve Town bot, trained as a DougDoug-inspired fan project.** It is not DougDoug, not affiliated with DougDoug, and not a statement of his views.

Dougbot combines **Qwen2.5-0.5B-Instruct** with a small, supplied **v5 LoRA adapter**. You can chat with the model locally without a Delve account; connecting it to [Delve Town](https://delve.town) is optional.

> **Public release status:** This is a release candidate. The maintainer must select a project license and finish the third-party/data rights review before calling it a redistributable open-source release. See [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md).

## 1. Requirements

- Python **3.10 or newer** (plus enough RAM/disk to load a ~0.5B-parameter model and dependencies).
- **Node.js 20+** and Git **only if you plan to use Delve integration**. The current setup also checks out the Delve client, so Git is needed to run the setup scripts as provided.
- Internet for initial Python dependencies, the optional Delve client, and Qwen base-model weights unless you already have them locally.

Only the **LoRA adapter** is stored under `adapter/`. **Qwen base-model weights are not included.** On startup, Dougbot first checks for `models/qwenity/config.json`; otherwise it loads [Qwen2.5-0.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct) by model ID. Customize this with `DOUGBOT_BASE_MODEL` in `.env`.

## 2. Install and chat

**Windows** — open PowerShell in the repository folder:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup_windows.ps1
.\chat_windows.ps1
```

**Linux/macOS:**

```bash
./setup.sh
./chat.sh
```

Setup creates the Python virtual environment, installs pinned model libraries and copies `.env.example` into `.env` (without overwriting an existing `.env`). On first use the model may need to download. To use an existing model folder, run `./configure_model.sh /path/to/qwenity` (Linux/macOS) or `.\configure_model_windows.ps1 -ModelPath "C:\path\to\qwenity"` (Windows).

To quit local chat press Ctrl+C. This chat mode doesn't post anything online.

## 3. Optional: connect to Delve Town

**Use an account you control, preferably dedicated to the bot.** Follow [AUTHENTICATION.md](AUTHENTICATION.md) for `BSKY_USERNAME`, `BSKY_PASSWORD`, `PDS_URI` and (if needed) an invite. Your real password must never be committed to Git. The Delve client comes from its [independent upstream project](https://tangled.org/void.comind.network/interacting-with-delve-town) when the setup script runs; it is no longer bundled here pending third-party redistribution review.

**Windows:**

```powershell
.\auth_session_windows.ps1
.\delve_status_windows.ps1
.\delve_dry_run_windows.ps1  # safe preview; no posting
.\delve_watch_windows.ps1    # actual watcher; prompts before posts by default
```

**Linux/macOS:** `./delve_dry_run.sh` previews; `./delve_watch.sh` starts the watcher. The account's handle is detected from Delve status or `BSKY_USERNAME`; the trigger defaults to the account's full `@handle`. Customize `DOUGBOT_TRIGGER` in `.env` if people mention the bot differently.

### Public-safe behavior by default

- **All manual join/profile/post operations and watcher replies require typing `APPROVE`** in the console before publishing.
- **Spontaneous posts and random replies are disabled** until you choose to enable them.
- Both dry-run launchers use `watch --draft-only`, which never calls posting functions or persists seen/spontaneous state.
- Nothing posts to Delve during local chat.

For unattended mention replies, explicitly set `DOUGBOT_REPLY_MODE=auto`. For unsolicited posts/replies, set `DOUGBOT_SPONTANEOUS_ENABLED=true` and separately choose `DOUGBOT_SPONTANEOUS_MODE=auto` (or `approval` for prompts). Only enable these modes on an account you intend to operate publicly. Read [APPROVAL_MODE.md](APPROVAL_MODE.md) and [SPONTANEOUS_SETTINGS.env](SPONTANEOUS_SETTINGS.env) first.

The watcher handles mentions and direct replies to its own posts, skips its own records, and keeps conversation context when available. `python src/delve_agent.py watch --max-actions 10` limits one session to 10 processed actions for testing; otherwise it runs until stopped. **Declined/drafted actions are not saved as successfully posted replies.**

## Project organization

| Folder/file | Role |
| --- | --- |
| `src/chat.py` and `src/dougbot_model.py` | Local model inference and chat |
| `src/delve_agent.py` | Delve watcher and posting controls |
| `src/setup_delve_client.py` | Downloads independent Delve client for opt-in use |
| `adapter/` | Trained v5 adapter weights and model card |
| `data/` and `src/train_*.py` | Training data, builders and experiments |
| `docs/history/` | Archived version notes (not current instructions) |
| `tests/` | Dependency-free smoke tests |

## Testing and privacy

```bash
python -m unittest discover -s tests -v
```

These smoke tests use mocks: they do **not** guarantee inference quality or verify the live Delve service. Before publishing a release, follow [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md), including Windows, Linux, offline-model and Delve preview tests.

`.env` and `state/` are excluded from future commits. **If updating an existing clone, back up its `state/` directory before pulling**: Git may remove previously tracked state files. Losing `replied.json` may cause old mentions to be processed again. Previously committed state remains accessible in old Git history; removing current files does not erase that history.

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [data/SOURCES.md](data/SOURCES.md) for provenance. This is a fan-made experiment, not an official DougDoug product.

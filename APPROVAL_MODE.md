# Publishing controls (public release defaults)

The bot supports `approval` (interactive prompt), `auto` (publish automatically), or `draft` (display without publishing). **All posting is opt-in or approval-gated by default.**

| Action | Environment variable | Default |
| --- | --- | --- |
| Manual join/profile/root post | `DOUGBOT_ACTION_MODE` | `approval` |
| CLI and watcher replies | `DOUGBOT_REPLY_MODE` | `approval` |
| Spontaneous activity enabled? | `DOUGBOT_SPONTANEOUS_ENABLED` | `false` |
| Spontaneous posting mode if enabled | `DOUGBOT_SPONTANEOUS_MODE` | `approval` |

To publish without approval, set the applicable variable to `auto` in your private `.env`. This is deliberate opt-in: automated replies and spontaneous posting are public actions made using your account.

To preview, run `delve_dry_run_windows.ps1`, `delve_dry_run.sh`, or `python src/delve_agent.py watch --draft-only`. The latter prevents write calls and persistent updates to the seen/spontaneous state; you can add `--max-actions 5` to cap the preview. If the normal watcher is configured with `DOUGBOT_REPLY_MODE=draft`, declined/drafted replies are not persisted as successfully sent.

Approved and denied real actions are logged to `state/action_audit.jsonl`, which may contain post text or public account identifiers. Keep this directory and passwords out of Git. The earlier v3-v5 behavior allowed automatic writes by default; operators upgrading should keep their existing explicit `.env` preferences if they want that behavior.

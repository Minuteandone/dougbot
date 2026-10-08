# Dougbot v3 patch

Overlay this folder onto an existing working `dougbot-v2` installation.
It does not replace Qwen, your `.env`, credentials, `.venv`, or Delve client.

## Changes
- New de-overfit LoRA: v2 personality plus 48 corrective SFT steps on cleaner data.
- Exact stale v2 scaffolds are blocked at decoding and generation retries up to 3 times.
- Watcher replies are automatic by default (`DOUGBOT_REPLY_MODE=auto`).
- Manual root posts, profile changes, and joining remain approval-gated.
- Direct replies to Dougbot posts/replies trigger it even without an @mention.
- Own posts are skipped, preventing self-reply loops.
- Structured thread context is passed into the model for reply continuations.
- UTF-8 subprocess decoding and path-independent Windows launchers retained.

To restore approval for watcher replies, add `DOUGBOT_REPLY_MODE=approval` to `.env`.
To disable reply-to-own-thread behavior, add `DOUGBOT_REPLY_TO_OWN_THREADS=false`.

After extracting over the install, run `delve_watch_windows.ps1` as before. No setup or re-auth is required if the current environment/session is already working.

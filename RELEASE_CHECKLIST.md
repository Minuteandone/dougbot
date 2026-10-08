# Release checklist: Dougbot public edition 📦

This document records **remaining work before announcing a downloadable / reusable public release**. The repository is already public, but public visibility is not itself an open-source license.

## Release blockers

- [ ] **Choose and add a project license.** The owner must select the license and confirm they can license all included original code and data. A license for Qwen does not automatically license Dougbot. GitHub's licensing guide: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository
- [ ] **Review model adapter/data redistribution rights.** Inspect `adapter/adapter_model.safetensors` and the complete `data/*.jsonl` sources and metadata, particularly VOD-inspired examples, Twitch/YouTube-derived material, Wikipedia/Fandom references and Delve conversations. Make sure the actual data included has the required permission/attribution and excludes personal/private content that shouldn't be redistributed. The model-card description is **not** evidence of permission.
- [ ] **Resolve the independent Delve client license.** The copied client was removed from the current tree pending verification; if it is ever bundled again, obtain permission/terms and preserve required notices. See `THIRD_PARTY_NOTICES.md`.
- [ ] **Review historical commits for secrets and private data.** Prior commits publicly exposed `state/action_audit.jsonl`, `state/replied.json`, and `state/spontaneous.json`, plus the old vendored client. Removing them from the latest tree does **not** remove that history. Rotate any exposed credentials and consider publishing from a fresh, checked tree/history if sensitive data must not remain available. A normal PR merge does not sanitize history.
- [ ] **Decide whether the release is code-only, code+LoRA adapter, or a full distributable package.** The current repo contains adapter weights, but not Qwen base weights. Do not promise a one-click self-contained download.

## Functional release testing

- [ ] Clone into a fresh directory on Windows, run `setup_windows.ps1` and `chat_windows.ps1` **without Node or Git**, to confirm local-only installation does not need Delve dependencies.
- [ ] Repeat fresh clone/install on Linux (and macOS if supported); test all shell launcher permissions.
- [ ] Test `DOUGBOT_BASE_MODEL` with a real local Qwen folder and with upstream download/cache.
- [ ] Confirm `python -m unittest discover -s tests -v` succeeds and CI smoke tests run.
- [ ] Install the optional independent Delve client with `src/setup_delve_client.py`, then with a dedicated Delve test account run `status` and `watch --draft-only --max-actions 5`: verify no posts and no state writes.
- [ ] Test approval-denied replies, one approved reply, and optional automatic replies; verify duplicates/self-replies are avoided and state survives restart.
- [ ] Enable spontaneous posting only by explicit configuration and check it respects the selected mode, cooldown and limits.
- [ ] Check logs and docs do not expose credentials; the repository must not contain a real `.env` or runtime state.

## Publishing

- [ ] Add a real project `LICENSE` file chosen by the owner (do not apply it retroactively to third-party components without permission).
- [ ] Confirm attribution and fan-project disclaimer on README/model card.
- [ ] Choose a release version/tag, describe supported Python/Node versions and any known limitations.
- [ ] Include an upgrade note to back up locally tracked `state/` before pulling this PR.
- [ ] Only after the blockers are resolved, merge the cleanup PR and tag a release.

Historical v2–v5 documents under `docs/history/` are preserved for reference, not installation instructions.

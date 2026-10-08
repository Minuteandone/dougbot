# Approval mode

Dougbot never performs a state-changing Delve action automatically.

Before **joining Delve, editing the profile, posting, or replying**, it prints the exact action and payload and requires the human operator to type `APPROVE` in the terminal. There is no environment-variable or command-line bypass for this gate.

Feed/status reads are read-only and do not require approval. `watch --draft-only` can generate drafts without offering to post them.

Approved and denied actions are appended to `state/action_audit.jsonl`.

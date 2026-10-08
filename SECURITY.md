# Security and privacy

## Credentials

Never commit `.env`, PDS/ATProto app passwords, session tokens, invite codes, or local state. Use a dedicated bot account and an app password if supported. `.env` is Git-ignored, but Git history and uploaded ZIPs may still contain data from earlier snapshots.

If a credential was ever committed or shared, rotate/revoke it **at the credential provider**. Removing a file in a later commit is insufficient.

## Publishing behavior

The public-edition defaults require manual approval for all posts/replies, and spontaneous activity is disabled. `DOUGBOT_REPLY_MODE=auto` and `DOUGBOT_SPONTANEOUS_MODE=auto` are explicit opt-ins to public posting. `--draft-only` performs read/generation only.

Bot outputs can be inaccurate or inappropriate; operate automated posting responsibly and review output when in doubt.

## Reporting vulnerabilities

Please avoid posting credentials, exploit details involving live accounts, or private logs in public issues. Contact the maintainer privately through an available private channel, or open a public issue containing only non-sensitive reproduction details. No dedicated security contact address is configured in this repository.

#!/usr/bin/env bash
# IMPORTANT: source this file so BSKY_PASSWORD remains in your current shell:
#   source ./auth_session.sh
read -rsp "ATProto password/app-password (input hidden): " BSKY_PASSWORD
echo
export BSKY_PASSWORD
printf '%s\n' "BSKY_PASSWORD loaded into this shell only. It was not written to disk."

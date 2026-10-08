#!/usr/bin/env bash
set -euo pipefail
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python src/setup_delve_client.py
[ -f .env ] || cp .env.example .env
printf '%s\n' 'Setup complete. Put/configure Qwen, edit .env, then run ./chat.sh.'

#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
[ -f .env ] || cp .env.example .env
printf '%s\n' 'Setup complete. Run ./chat.sh. For optional Delve use, run .venv/bin/python src/setup_delve_client.py.'

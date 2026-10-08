#!/usr/bin/env bash
set -euo pipefail
. .venv/bin/activate
python src/delve_agent.py watch

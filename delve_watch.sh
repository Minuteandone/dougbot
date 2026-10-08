#!/usr/bin/env bash
set -euo pipefail
"$(dirname "$0")/.venv/bin/python" "$(dirname "$0")/src/delve_agent.py" watch

#!/usr/bin/env bash
set -euo pipefail
MODEL_PATH="${1:?usage: ./configure_model.sh /path/to/qwenity}"
test -f "$MODEL_PATH/config.json" || { echo "config.json not found" >&2; exit 1; }
test -f "$MODEL_PATH/model.safetensors" || { echo "model.safetensors not found" >&2; exit 1; }
[ -f .env ] || cp .env.example .env
python - "$MODEL_PATH" <<'PY'
from pathlib import Path
import sys
p=Path('.env'); model=str(Path(sys.argv[1]).resolve())
lines=p.read_text().splitlines(); out=[]; found=False
for line in lines:
    if line.startswith('DOUGBOT_BASE_MODEL='):
        out.append('DOUGBOT_BASE_MODEL='+model); found=True
    else: out.append(line)
if not found: out.append('DOUGBOT_BASE_MODEL='+model)
p.write_text('\n'.join(out)+'\n')
PY
echo "Configured Dougbot to use $MODEL_PATH"

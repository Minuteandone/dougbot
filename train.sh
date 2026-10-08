#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
"$ROOT/.venv/bin/python" "$ROOT/src/train_lora_strong.py" --base "$ROOT/models/qwenity" --data "$ROOT/data/train.jsonl" --out "$ROOT/adapter-retrained" --steps 80 --lr 0.00028 --max-length 52 --rank 8 --alpha 16

$ErrorActionPreference = "Stop"
$base = Join-Path $PSScriptRoot "models\qwenity"
$data = Join-Path $PSScriptRoot "data\train.jsonl"
$out = Join-Path $PSScriptRoot "adapter-retrained"
& "$PSScriptRoot\.venv\Scripts\python.exe" "$PSScriptRoot\src\train_lora_strong.py" --base $base --data $data --out $out --steps 80 --lr 0.00028 --max-length 52 --rank 8 --alpha 16

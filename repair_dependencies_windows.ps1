$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Dougbot .venv was not found at $python. Run setup_windows.ps1 first."
}

Write-Host "Repairing Dougbot's model-library versions..." -ForegroundColor Cyan
& $python -m pip install --upgrade --force-reinstall `
    "transformers==4.57.1" `
    "tokenizers==0.22.1" `
    "peft==0.17.1" `
    "accelerate==1.10.1" `
    "huggingface-hub>=0.34,<1.0"

Write-Host "Running tokenizer compatibility test..." -ForegroundColor Cyan
$test = @'
from pathlib import Path
import transformers, tokenizers, peft, accelerate, huggingface_hub
from transformers import AutoTokenizer
root = Path.cwd()
model = root / "models" / "qwenity"
assert (model / "tokenizer.json").exists(), f"Missing {model / 'tokenizer.json'}"
tok = AutoTokenizer.from_pretrained(str(model), use_fast=True, local_files_only=True)
print("transformers", transformers.__version__)
print("tokenizers", tokenizers.__version__)
print("peft", peft.__version__)
print("accelerate", accelerate.__version__)
print("huggingface-hub", huggingface_hub.__version__)
print("Tokenizer:", type(tok).__name__)
print("Token test:", tok("hello", add_special_tokens=False)["input_ids"])
'@
& $python -c $test

Write-Host "Compatibility repair passed. Re-run auth_session_windows.ps1, then delve_watch_windows.ps1." -ForegroundColor Green

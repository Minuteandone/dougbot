$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Test-Path .venv)) { py -m venv .venv }
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
Write-Host "Setup complete. Run chat_windows.ps1. For optional Delve use, run .\.venv\Scripts\python.exe .\src\setup_delve_client.py first." -ForegroundColor Green

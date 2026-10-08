$ErrorActionPreference = "Stop"
if (-not (Test-Path .venv)) { py -m venv .venv }
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src\setup_delve_client.py
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
Write-Host "Setup complete. Put/configure Qwen, edit .env, then run chat_windows.ps1." -ForegroundColor Green

param([Parameter(Mandatory=$true)][string]$ModelPath)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Test-Path (Join-Path $ModelPath "config.json"))) { throw "config.json not found in $ModelPath" }
if (-not (Test-Path (Join-Path $ModelPath "model.safetensors"))) { throw "model.safetensors not found in $ModelPath" }
if (-not (Test-Path ".env")) { Copy-Item "$PSScriptRoot\.env.example" "$PSScriptRoot\.env" }
$escaped=$ModelPath.Replace("\\","/")
$lines=Get-Content "$PSScriptRoot\.env"
$found=$false
$lines=$lines | ForEach-Object {
  if ($_ -match '^DOUGBOT_BASE_MODEL=') { $found=$true; "DOUGBOT_BASE_MODEL=$escaped" } else { $_ }
}
if (-not $found) { $lines += "DOUGBOT_BASE_MODEL=$escaped" }
$lines | Set-Content "$PSScriptRoot\.env"
Write-Host "Configured Dougbot to use $ModelPath" -ForegroundColor Green

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$secure = Read-Host "ATProto password/app-password (input hidden)" -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
    $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    $env:BSKY_PASSWORD = $plain
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    Remove-Variable plain -ErrorAction SilentlyContinue
}
Write-Host "BSKY_PASSWORD loaded into this PowerShell process only. It was not written to disk." -ForegroundColor Green
Write-Host "Now run: .\delve_status_windows.ps1 or .\delve_watch_windows.ps1" -ForegroundColor Cyan

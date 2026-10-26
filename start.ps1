param(
    [int]$Port = 8000
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.venv\Scripts\python.exe')) { throw 'Run setup.ps1 first.' }
if (-not (Test-Path 'frontend\dist\index.html')) { throw 'Build the frontend using setup.ps1 first.' }
Write-Host "Attend is starting at http://127.0.0.1:$Port — press Ctrl+C to stop."
& '.\.venv\Scripts\python.exe' -m uvicorn backend.main:app --host 127.0.0.1 --port $Port


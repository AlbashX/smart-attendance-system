param(
    [int]$Port = 8000
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

if (-not (Test-Path '.venv\Scripts\python.exe')) { throw 'Run setup.ps1 first.' }
if (-not (Test-Path 'frontend\dist\index.html')) { throw 'Build the frontend using setup.ps1 first.' }

$LanIp = (
    Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object {
        $_.IPAddress -notlike '127.*' -and
        $_.IPAddress -notlike '169.254*' -and
        $_.InterfaceAlias -notlike '*WSL*' -and
        $_.InterfaceAlias -notlike 'vEthernet*'
    } |
    Sort-Object { if ($_.InterfaceAlias -like 'Wi-Fi*') { 0 } else { 1 } } |
    Select-Object -First 1 -ExpandProperty IPAddress
)

Write-Host "Attend is starting. Keep this window open. Press Ctrl+C to stop."
Write-Host "This PC:     http://127.0.0.1:${Port}"
if ($LanIp) {
    Write-Host "Phone/LAN:   http://${LanIp}:${Port}"
    Write-Host "Phone must be on the same Wi-Fi (or this PC's hotspot). Guest/campus Wi-Fi often blocks device-to-device access."
} else {
    Write-Host "No LAN IPv4 found. This PC can still use http://127.0.0.1:${Port}"
}

& '.\.venv\Scripts\python.exe' -m uvicorn backend.main:app --host 0.0.0.0 --port $Port

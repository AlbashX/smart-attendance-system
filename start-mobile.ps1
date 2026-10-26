param([string]$Address)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not $Address) {
    $Address = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -eq 'Wi-Fi' -and $_.IPAddress -notlike '169.254*' } | Select-Object -First 1).IPAddress
}
if (-not $Address) { throw 'Supply the laptop LAN address: .\start-mobile.ps1 -Address 192.168.1.10' }
& '.\.venv\Scripts\python.exe' -c 'import cryptography'
if ($LASTEXITCODE -ne 0) { throw 'Install mobile dependencies: .\.venv\Scripts\python.exe -m pip install -r requirements-mobile.txt' }
& '.\.venv\Scripts\python.exe' scripts/mobile_server.py --init $Address
if ($LASTEXITCODE -ne 0) { throw 'Certificate setup failed.' }
Write-Host 'Keep start.ps1 running in another terminal. Read docs/mobile-access.md for phone setup.'
& '.\.venv\Scripts\python.exe' scripts/mobile_server.py

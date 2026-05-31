#!/usr/bin/env pwsh

$Green = "`e[0;32m"
$Yellow = "`e[1;33m"
$Red = "`e[0;31m"
$NC = "`e[0m"

function Write-Info {
    param([string]$Msg, [string]$Color = $NC)
    Write-Host "$Color$Msg$NC"
}

Write-Host ""
Write-Host "==================================================="
Write-Host "   Historical Starlink - Service Status"
Write-Host "==================================================="
Write-Host ""

$backendOk = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }
if ($backendOk) {
    Write-Info "[OK] Backend  : http://localhost:8000" $Green
    Write-Info "     API docs : http://localhost:8000/docs" $Green
    Write-Info "     Health   : http://localhost:8000/health" $Green
} else {
    Write-Info "[--] Backend is NOT running" $Red
}

Write-Host ""

$frontendOk = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }
if ($frontendOk) {
    Write-Info "[OK] Frontend : http://localhost:3000" $Green
} else {
    Write-Info "[--] Frontend is NOT running" $Red
}

Write-Host ""
Write-Host "==================================================="
Write-Host ""
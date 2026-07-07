#!/usr/bin/env pwsh

$Green = "`e[0;32m"
$Yellow = "`e[1;33m"
$Red = "`e[0;31m"
$NC = "`e[0m"

function Write-Info {
    param([string]$Msg, [string]$Color = $NC)
    Write-Host "$Color$Msg$NC"
}

$ProjectRoot = $PSScriptRoot

function Read-Env {
    param([string]$Key, [string]$Default)
    $envFile = Join-Path $ProjectRoot ".env"
    if (Test-Path $envFile) {
        foreach ($line in Get-Content $envFile -Encoding UTF8) {
            $line = $line.Trim()
            if ($line -match "^$Key=(.*)$") {
                return $Matches[1].Trim()
            }
        }
    }
    return $Default
}

$BackendPort = [int](Read-Env "SERVER_PORT" "8000")
$FrontendPort = [int](Read-Env "FRONTEND_PORT" "3000")

Write-Host ""
Write-Host "==================================================="
Write-Host "   Historical Starlink - Service Status"
Write-Host "==================================================="
Write-Host ""

$backendOk = Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }
if ($backendOk) {
    Write-Info "[OK] Backend  : http://localhost:$BackendPort" $Green
    Write-Info "     API docs : http://localhost:$BackendPort/docs" $Green
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:$BackendPort/health" -TimeoutSec 5
        Write-Info "     Health   : $($health.status)" $Green
    } catch {
        Write-Info "     Health   : port open, health check failed" $Yellow
    }
} else {
    Write-Info "[--] Backend is NOT running" $Red
}

Write-Host ""

$frontendOk = Get-NetTCPConnection -LocalPort $FrontendPort -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }
if ($frontendOk) {
    Write-Info "[OK] Frontend : http://localhost:$FrontendPort" $Green
} else {
    Write-Info "[--] Frontend is NOT running" $Red
}

Write-Host ""
Write-Host "==================================================="
Write-Host ""

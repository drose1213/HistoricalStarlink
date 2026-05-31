#!/usr/bin/env pwsh

$Green = "`e[0;32m"
$Yellow = "`e[1;33m"
$Red = "`e[0;31m"
$NC = "`e[0m"

function Write-Info {
    param([string]$Msg, [string]$Color = $NC)
    Write-Host "$Color$Msg$NC"
}

function Stop-Port {
    param([int]$Port, [string]$Name)
    Write-Info "Stopping $Name (port $Port)..." $Yellow
    $conns = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
             Where-Object { $_.State -eq "Listen" } |
             Select-Object -ExpandProperty OwningProcess -Unique
    if ($conns) {
        foreach ($processId in $conns) {
            $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Info "  Killed $($proc.ProcessName) (PID $processId)" $Red
                Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
            }
        }
    } else {
        Write-Info "  Port $Port is already free" $Green
    }
}

Write-Host ""
Write-Host "==================================================="
Write-Host "   Historical Starlink - Stop Services"
Write-Host "==================================================="
Write-Host ""

Stop-Port -Port 8000 -Name "Backend"
Stop-Port -Port 3000 -Name "Frontend"

taskkill /FI "WINDOWTITLE eq Backend*" /F 2>&1 | Out-Null
taskkill /FI "WINDOWTITLE eq Frontend*" /F 2>&1 | Out-Null

$pidFiles = @(".backend.pid", ".frontend.pid")
foreach ($f in $pidFiles) {
    $fp = Join-Path $PSScriptRoot $f
    if (Test-Path $fp) {
        Remove-Item $fp -Force -ErrorAction SilentlyContinue
    }
}

Write-Host ""
Write-Info "All services stopped." $Green
Write-Host ""

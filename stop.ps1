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

function Stop-ProcessTree {
    param([int]$ProcessId, [string]$Name)
    $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if (-not $proc) {
        return
    }

    $children = Get-CimInstance Win32_Process -Filter "ParentProcessId=$ProcessId" -ErrorAction SilentlyContinue
    foreach ($child in $children) {
        Stop-ProcessTree -ProcessId ([int]$child.ProcessId) -Name $Name
    }

    Write-Info "  Killed $Name process $($proc.ProcessName) (PID $ProcessId)" $Red
    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
}

function Stop-PidFile {
    param([string]$FileName, [string]$Name)
    $path = Join-Path $ProjectRoot $FileName
    if (-not (Test-Path $path)) {
        return
    }

    $raw = (Get-Content $path -ErrorAction SilentlyContinue | Select-Object -First 1)
    $processId = 0
    if ([int]::TryParse($raw, [ref]$processId)) {
        Stop-ProcessTree -ProcessId $processId -Name $Name
    }
    Remove-Item $path -Force -ErrorAction SilentlyContinue
}

function Stop-WorkspaceFrontendServers {
    $escapedRoot = [regex]::Escape($ProjectRoot)
    $processes = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            $_.CommandLine -and
            $_.CommandLine -match $escapedRoot -and
            ($_.CommandLine -match 'vite|npm-cli\.js')
        }

    foreach ($proc in $processes) {
        Stop-ProcessTree -ProcessId ([int]$proc.ProcessId) -Name "Frontend"
    }
}

$BackendPort = [int](Read-Env "SERVER_PORT" "8000")
$FrontendPort = [int](Read-Env "FRONTEND_PORT" "3000")

Write-Host ""
Write-Host "==================================================="
Write-Host "   Historical Starlink - Stop Services"
Write-Host "==================================================="
Write-Host ""

Stop-PidFile -FileName ".backend.pid" -Name "Backend"
Stop-PidFile -FileName ".frontend.pid" -Name "Frontend"
Stop-WorkspaceFrontendServers
Stop-Port -Port $BackendPort -Name "Backend"
Stop-Port -Port $FrontendPort -Name "Frontend"

taskkill /FI "WINDOWTITLE eq Backend*" /F 2>&1 | Out-Null
taskkill /FI "WINDOWTITLE eq Frontend*" /F 2>&1 | Out-Null

$pidFiles = @(".backend.pid", ".frontend.pid")
foreach ($f in $pidFiles) {
    $fp = Join-Path $ProjectRoot $f
    if (Test-Path $fp) {
        Remove-Item $fp -Force -ErrorAction SilentlyContinue
    }
}

Write-Host ""
Write-Info "All services stopped." $Green
Write-Host ""

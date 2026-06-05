#!/usr/bin/env pwsh
$ProjectRoot = $PSScriptRoot

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
    $conns = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
             Where-Object { $_.State -eq "Listen" } |
             Select-Object -ExpandProperty OwningProcess -Unique
    if ($conns) {
        foreach ($processId in $conns) {
            $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Info "  Killing $($proc.ProcessName) (PID $processId)" $Red
                Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
            }
        }
    } else {
        Write-Info "  Port $Port is free" $Green
    }
}

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

function Test-MySQL {
    Write-Info "Checking MySQL..." $Yellow
    $pwd = Read-Env "MYSQL_PASSWORD" "root"
    $host_ = Read-Env "MYSQL_HOST" "127.0.0.1"
    $port = Read-Env "MYSQL_PORT" "3306"
    $user = Read-Env "MYSQL_USER" "root"
    try {
        $env:MYSQL_PWD = $pwd
        & mysql -u $user -h $host_ -P $port -e "SELECT 1" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Info "  MySQL OK ($host_`:$port)" $Green
            return
        }
    } catch {}
    Write-Info "  MySQL CLI not found or not running (non-fatal)" $Yellow
}

function Test-Redis {
    Write-Info "Checking Redis..." $Yellow
    try {
        $r = & redis-cli ping 2>&1
        if ($r -eq "PONG") {
            Write-Info "  Redis OK" $Green
            return
        }
    } catch {}
    Write-Info "  Redis not found or not running (non-fatal)" $Yellow
}

function Init-DB {
    Write-Info "Creating database if not exists..." $Yellow
    $pwd = Read-Env "MYSQL_PASSWORD" "root"
    $host_ = Read-Env "MYSQL_HOST" "127.0.0.1"
    $port = Read-Env "MYSQL_PORT" "3306"
    $user = Read-Env "MYSQL_USER" "root"
    $db = Read-Env "MYSQL_DATABASE" "historical_starlink"
    $sql = "CREATE DATABASE IF NOT EXISTS $db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    try {
        $env:MYSQL_PWD = $pwd
        & mysql -u $user -h $host_ -P $port -e $sql 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Info "  Database '$db' ready" $Green
        } else {
            Write-Info "  [WARN] Auto-create DB failed" $Yellow
        }
    } catch {
        Write-Info "  [WARN] mysql CLI not found, ensure DB '$db' exists" $Yellow
    }
}

Write-Host ""
Write-Host "==================================================="
Write-Host "   Historical Starlink - Start Services"
Write-Host "==================================================="
Write-Host ""

Write-Info "[1/6] Stopping old processes..." $Yellow
Stop-Port -Port 8000 -Name "Backend"
Stop-Port -Port 3000 -Name "Frontend"
Write-Host ""

Write-Info "[2/6] Checking MySQL..." $Yellow
Test-MySQL
Write-Host ""

Write-Info "[3/6] Checking Redis..." $Yellow
Test-Redis
Write-Host ""

Write-Info "[4/6] Creating database..." $Yellow
Init-DB
Write-Host ""

Write-Info "[5/6] Setting up backend..." $Yellow
$venvDir = Join-Path $ProjectRoot "venv"
if (-not (Test-Path $venvDir)) {
    Write-Info "  Creating Python venv..." $Yellow
    python -m venv $venvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Info "  [ERROR] Failed to create venv" $Red
        exit 1
    }
}

$activateScript = Join-Path $venvDir "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    . $activateScript
}

Write-Info "  Installing Python dependencies..." $Yellow
pip install -r (Join-Path $ProjectRoot "backend\requirements.txt") --quiet 2>&1 | Out-Null

Write-Info "  Starting uvicorn on port 8000..." $Yellow
$backendProc = Start-Process -FilePath "python" `
    -ArgumentList "-m","uvicorn","backend.main:app","--host","0.0.0.0","--port","8000","--reload" `
    -WorkingDirectory $ProjectRoot -PassThru -WindowStyle Minimized
$backendProc.Id | Out-File (Join-Path $ProjectRoot ".backend.pid") -Encoding ASCII
Write-Info "  Backend PID: $($backendProc.Id)" $Green

Write-Info "  Waiting for backend to listen on port 8000..." $Yellow
$waited = 0
$backendReady = $false
while ($waited -lt 60) {
    $listener = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    if ($listener) {
        $backendReady = $true
        break
    }
    Start-Sleep -Seconds 1
    $waited += 1
}
if (-not $backendReady) {
    Write-Info "  [WARN] Backend did not start listening within 60s, continuing anyway" $Yellow
} else {
    Write-Info "  Backend is listening (waited ${waited}s)" $Green
}
Write-Host ""

Write-Info "[6/6] Setting up frontend..." $Yellow
$frontendDir = Join-Path $ProjectRoot "frontend"
$npmCommand = Get-Command "npm.cmd" -ErrorAction SilentlyContinue
if (-not $npmCommand) {
    Write-Info "  [ERROR] npm.cmd not found. Please install Node.js or add it to PATH." $Red
    exit 1
}

if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    Write-Info "  Installing npm dependencies..." $Yellow
    Push-Location $frontendDir
    & $npmCommand.Source install --silent 2>&1 | Out-Null
    Pop-Location
}

Write-Info "  Starting vite on port 3000..." $Yellow
$frontendProc = Start-Process -FilePath $npmCommand.Source `
    -ArgumentList "run","dev" `
    -WorkingDirectory $frontendDir -PassThru -WindowStyle Minimized
$frontendProc.Id | Out-File (Join-Path $ProjectRoot ".frontend.pid") -Encoding ASCII
Write-Info "  Frontend PID: $($frontendProc.Id)" $Green
Start-Sleep -Seconds 3
Write-Host ""

Write-Host "==================================================="
Write-Host "   All services started!"
Write-Host "==================================================="
Write-Host ""
Write-Info "   Frontend:  http://localhost:3000" $Green
Write-Info "   API docs:  http://localhost:8000/docs" $Green
Write-Info "   Health:    http://localhost:8000/health" $Green
Write-Host ""
Write-Info "   Stop:      .\stop.ps1" $Green
Write-Info "   Status:    .\status.ps1" $Green
Write-Host ""
Write-Host "==================================================="
Write-Host ""

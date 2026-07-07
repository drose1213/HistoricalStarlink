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

    Write-Info "  Killing $Name process $($proc.ProcessName) (PID $ProcessId)" $Red
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
Stop-PidFile -FileName ".backend.pid" -Name "Backend"
Stop-PidFile -FileName ".frontend.pid" -Name "Frontend"
Stop-WorkspaceFrontendServers
Stop-Port -Port $BackendPort -Name "Backend"
Stop-Port -Port $FrontendPort -Name "Frontend"
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

Write-Info "  Starting uvicorn on port $BackendPort..." $Yellow
$venvPython = Join-Path $venvDir "Scripts\python.exe"
$backendLog = Join-Path $ProjectRoot "backend\uvicorn.log"
$backendErrLog = Join-Path $ProjectRoot "backend\uvicorn_err.log"
# 使用 venv python 直接启动, -u 禁用输出缓冲确保日志实时写入
# 标准输出和错误输出分别重定向 (PowerShell 不允许指向同一文件)
$backendProc = Start-Process -FilePath $venvPython `
    -ArgumentList "-u", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "$BackendPort", "--app-dir", $ProjectRoot `
    -WorkingDirectory $ProjectRoot `
    -RedirectStandardOutput $backendLog `
    -RedirectStandardError $backendErrLog `
    -PassThru -NoNewWindow
$backendProc.Id | Out-File (Join-Path $ProjectRoot ".backend.pid") -Encoding ASCII
Write-Info "  Backend PID: $($backendProc.Id)" $Green

Write-Info "  Waiting for backend to listen on port $BackendPort..." $Yellow
$waited = 0
$backendReady = $false
while ($waited -lt 60) {
    $listener = Get-NetTCPConnection -LocalPort $BackendPort -State Listen -ErrorAction SilentlyContinue
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
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:$BackendPort/health" -TimeoutSec 5
        Write-Info "  Backend health: $($health.status)" $Green
    } catch {
        Write-Info "  [WARN] Backend port is open but /health did not respond" $Yellow
    }
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

Write-Info "  Starting vite on port $FrontendPort..." $Yellow
$frontendProc = Start-Process -FilePath $npmCommand.Source `
    -ArgumentList "run","dev","--","--host","127.0.0.1","--port","$FrontendPort","--strictPort" `
    -WorkingDirectory $frontendDir -PassThru -WindowStyle Minimized
$frontendProc.Id | Out-File (Join-Path $ProjectRoot ".frontend.pid") -Encoding ASCII
Write-Info "  Frontend PID: $($frontendProc.Id)" $Green
Write-Info "  Waiting for frontend to listen on port $FrontendPort..." $Yellow
$frontendReady = $false
for ($i = 0; $i -lt 30; $i++) {
    $frontendListener = Get-NetTCPConnection -LocalPort $FrontendPort -State Listen -ErrorAction SilentlyContinue
    if ($frontendListener) {
        $frontendReady = $true
        break
    }
    Start-Sleep -Seconds 1
}
if (-not $frontendReady) {
    Write-Info "  [WARN] Frontend did not start on port $FrontendPort. Check frontend dev server output." $Yellow
} else {
    Write-Info "  Frontend is listening on port $FrontendPort" $Green
}
Write-Host ""

Write-Host "==================================================="
Write-Host "   All services started!"
Write-Host "==================================================="
Write-Host ""
Write-Info "   Frontend:  http://localhost:$FrontendPort" $Green
Write-Info "   API docs:  http://localhost:$BackendPort/docs" $Green
Write-Info "   Health:    http://localhost:$BackendPort/health" $Green
Write-Host ""
Write-Info "   Stop:      .\stop.ps1" $Green
Write-Info "   Status:    .\status.ps1" $Green
Write-Host ""
Write-Host "==================================================="
Write-Host ""

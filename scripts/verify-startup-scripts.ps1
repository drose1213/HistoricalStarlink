#!/usr/bin/env pwsh

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$StartScript = Join-Path $ProjectRoot "start.ps1"
$StopScript = Join-Path $ProjectRoot "stop.ps1"

function Assert-Condition {
    param(
        [bool]$Condition,
        [string]$Message
    )

    if (-not $Condition) {
        throw $Message
    }
}

$startContent = Get-Content -LiteralPath $StartScript -Raw -Encoding UTF8
$stopContent = Get-Content -LiteralPath $StopScript -Raw -Encoding UTF8
$statusContent = Get-Content -LiteralPath (Join-Path $ProjectRoot "status.ps1") -Raw -Encoding UTF8

Assert-Condition ($startContent -notmatch 'foreach\s*\(\s*\$pid\b') "start.ps1 must not use reserved PowerShell variable `$pid as a loop variable."
Assert-Condition ($stopContent -notmatch 'foreach\s*\(\s*\$pid\b') "stop.ps1 must not use reserved PowerShell variable `$pid as a loop variable."
Assert-Condition ($startContent -notmatch 'Start-Process\s+-FilePath\s+"npm"') "start.ps1 must not launch bare npm because Windows may resolve it to npm.ps1 or npm."
Assert-Condition ($startContent -match 'npm\.cmd') "start.ps1 must launch npm.cmd explicitly for the frontend dev server."
Assert-Condition ($startContent -match 'FRONTEND_PORT') "start.ps1 must read FRONTEND_PORT instead of hard-coding the frontend port."
Assert-Condition ($startContent -match '--strictPort') "start.ps1 must start Vite with --strictPort so it cannot silently move ports."
Assert-Condition ($statusContent -match 'FRONTEND_PORT') "status.ps1 must read FRONTEND_PORT instead of hard-coding the frontend status port."
Assert-Condition ($stopContent -match 'FRONTEND_PORT') "stop.ps1 must read FRONTEND_PORT instead of hard-coding the frontend stop port."
Assert-Condition ($stopContent -match 'Stop-ProcessTree') "stop.ps1 must stop pid-file process trees so child Vite/Uvicorn processes are cleaned up."
Assert-Condition ($startContent -match 'Stop-WorkspaceFrontendServers') "start.ps1 must clean stale Vite processes from this project before launching."
Assert-Condition ($stopContent -match 'Stop-WorkspaceFrontendServers') "stop.ps1 must clean stale Vite processes from this project."

Write-Output "startup script checks passed"

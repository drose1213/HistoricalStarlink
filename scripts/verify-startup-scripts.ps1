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

Assert-Condition ($startContent -notmatch 'foreach\s*\(\s*\$pid\b') "start.ps1 must not use reserved PowerShell variable `$pid as a loop variable."
Assert-Condition ($stopContent -notmatch 'foreach\s*\(\s*\$pid\b') "stop.ps1 must not use reserved PowerShell variable `$pid as a loop variable."
Assert-Condition ($startContent -notmatch 'Start-Process\s+-FilePath\s+"npm"') "start.ps1 must not launch bare npm because Windows may resolve it to npm.ps1 or npm."
Assert-Condition ($startContent -match 'npm\.cmd') "start.ps1 must launch npm.cmd explicitly for the frontend dev server."

Write-Output "startup script checks passed"

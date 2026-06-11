$src = "d:\Ai\workspace\HistoricalStarlink\frontend\landing_screenshots"
$dst = "d:\Ai\workspace\HistoricalStarlink\frontend\public\demo"

Get-ChildItem -Path $src -Filter *.png | ForEach-Object {
    $newName = "landing_$($_.Name)"
    $destPath = Join-Path $dst $newName
    Copy-Item -Path $_.FullName -Destination $destPath -Force
    Write-Host "Copied $($_.Name) -> $newName"
}

Write-Host "---"
Write-Host "Final contents of demo directory:"
Get-ChildItem -Path $dst | Select-Object Name, Length

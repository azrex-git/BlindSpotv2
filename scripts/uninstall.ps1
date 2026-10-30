# Standalone PowerShell Uninstaller for BlindSpot1 / BlindSpot
param(
    [switch]$Force,
    [switch]$CleanConfig
)

Write-Host "● BlindSpot1 / BlindSpot System Cleanup" -ForegroundColor Cyan

$shims = @(
    "$HOME\.local\bin\blindspot1.cmd",
    "$HOME\.local\bin\blindspot1.ps1",
    "$HOME\.local\bin\blindspot.cmd",
    "$HOME\.local\bin\blindspot.ps1",
    "$HOME\.blindspot\bin\blindspot1.cmd",
    "$HOME\.blindspot\bin\blindspot1.ps1",
    "$HOME\.blindspot\bin\blindspot.cmd",
    "$HOME\.blindspot\bin\blindspot.ps1",
    "$HOME\AppData\Local\Python\bin\blindspot1.cmd",
    "$HOME\AppData\Local\Python\bin\blindspot1.ps1",
    "$HOME\AppData\Local\Python\bin\blindspot.cmd",
    "$HOME\AppData\Local\Python\bin\blindspot.ps1"
)

if (-not $Force) {
    $confirm = Read-Host "Are you sure you want to remove BlindSpot1 command shims and packages? (y/N)"
    if ($confirm -ne "y" -and $confirm -ne "yes") {
        Write-Host "Uninstallation aborted." -ForegroundColor Yellow
        exit 0
    }
}

foreach ($s in $shims) {
    if (Test-Path $s) {
        Remove-Item $s -Force
        Write-Host "  ✓ Removed: $s" -ForegroundColor Green
    }
}

# Uninstall pip and uv packages
try {
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        uv tool uninstall blindspot1 *>$null
    }
    py -m pip uninstall -y blindspot1 blindspot *>$null
    python -m pip uninstall -y blindspot1 blindspot *>$null
    Write-Host "  ✓ Package uninstalled from Python / uv" -ForegroundColor Green
} catch {
    Write-Host "  ! Python pip uninstall skipped" -ForegroundColor DarkGray
}

if ($CleanConfig) {
    $cfgPath = "$HOME\.blindspot"
    if (Test-Path $cfgPath) {
        Remove-Item $cfgPath -Recurse -Force
        Write-Host "  ✓ Removed configuration directory $cfgPath" -ForegroundColor Green
    }
}

Write-Host "`n✓ Cleanup completed successfully." -ForegroundColor Green

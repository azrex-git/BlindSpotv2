# One-command Windows uninstaller. Configuration is kept unless -CleanConfig is supplied.
# irm https://raw.githubusercontent.com/harshit-dev-on/blind-spot/main/scripts/uninstall.ps1 | iex
param([switch]$CleanConfig)

$ErrorActionPreference = "Stop"
$BlindSpotHome = Join-Path $HOME ".blindspot"
$InstallDir = Join-Path $BlindSpotHome "bin"
$HomeFullPath = [System.IO.Path]::GetFullPath($HOME).TrimEnd('\')
$BlindSpotHomeFullPath = [System.IO.Path]::GetFullPath($BlindSpotHome).TrimEnd('\')

if ($env:BLINDSPOT_CLEAN_CONFIG -eq "1") { $CleanConfig = $true }

if (-not $env:BLINDSPOT_UNINSTALL_FORCE) {
    $answer = Read-Host "Remove BlindSpot and its managed Python environment? Configuration will be kept. (y/N)"
    if ($answer -notin @("y", "yes")) {
        Write-Host "Uninstallation cancelled." -ForegroundColor Yellow
        return
    }
}

foreach ($name in @("blindspot.cmd", "blindspot.ps1", "blindspot.bat", "blindspot.exe", "blindspot1.cmd", "blindspot1.ps1", "blindspot1.bat", "blindspot1.exe")) {
    $shim = Join-Path $InstallDir $name
    if (Test-Path -LiteralPath $shim) {
        Remove-Item -LiteralPath $shim -Force
        Write-Host "Removed $shim"
    }
}

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$userEntries = @($userPath -split ";" | Where-Object { $_ -and $_.TrimEnd('\') -ine $InstallDir.TrimEnd('\') })
[Environment]::SetEnvironmentVariable("Path", ($userEntries -join ";"), "User")

function Remove-BlindSpotManagedDirectory {
    param([string]$Path, [string]$ExpectedParent, [string[]]$AllowedNames)
    $fullPath = [System.IO.Path]::GetFullPath($Path).TrimEnd('\')
    $fullParent = [System.IO.Path]::GetFullPath((Split-Path -Parent $fullPath)).TrimEnd('\')
    $expected = [System.IO.Path]::GetFullPath($ExpectedParent).TrimEnd('\')
    $leaf = Split-Path -Leaf $fullPath
    if ($fullParent -ine $expected -or $leaf -notin $AllowedNames) {
        throw "Refusing to remove unexpected path: $fullPath"
    }
    if (Test-Path -LiteralPath $fullPath) {
        Remove-Item -LiteralPath $fullPath -Recurse -Force
        Write-Host "Removed $fullPath"
    }
}

Remove-BlindSpotManagedDirectory (Join-Path $BlindSpotHome "venv-py312") $BlindSpotHome @("venv-py312")
Remove-BlindSpotManagedDirectory (Join-Path $BlindSpotHome "uv") $BlindSpotHome @("uv")

if ($CleanConfig) {
    Remove-BlindSpotManagedDirectory $BlindSpotHome $HOME @(".blindspot")
} elseif ((Test-Path -LiteralPath $InstallDir) -and -not (Get-ChildItem -LiteralPath $InstallDir -Force | Select-Object -First 1)) {
    Remove-Item -LiteralPath $InstallDir -Force
}

Write-Host "BlindSpot was removed. Open a new terminal to refresh PATH." -ForegroundColor Green
if (-not $CleanConfig) {
    Write-Host "Saved configuration and bridge data remain under $BlindSpotHome."
    Write-Host "Run again with -CleanConfig to remove that data too."
}

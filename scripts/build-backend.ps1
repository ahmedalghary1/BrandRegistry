Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$specFile = Join-Path $projectRoot "brandregistry-backend.spec"
$distDir = Join-Path $projectRoot "dist"
$buildDir = Join-Path $projectRoot "build"
$backendDistName = "brandregistry-backend"
$backendDistDir = Join-Path $distDir $backendDistName
$electronBackendRoot = Join-Path $projectRoot "electron\resources\backend"
$electronBackendDir = Join-Path $electronBackendRoot $backendDistName
$venvPyInstaller = Join-Path $projectRoot ".venv\Scripts\pyinstaller.exe"

if (Test-Path $venvPyInstaller) {
    $pyInstallerCommand = $venvPyInstaller
} else {
    $pyInstallerCommand = "pyinstaller"
}

Write-Host "Building desktop backend with PyInstaller..."
Push-Location $projectRoot
try {
    if (Test-Path $buildDir) {
        Remove-Item $buildDir -Recurse -Force
    }

    if (Test-Path $backendDistDir) {
        Remove-Item $backendDistDir -Recurse -Force
    }

    & $pyInstallerCommand --noconfirm --clean $specFile

    if (-not (Test-Path $backendDistDir)) {
        throw "PyInstaller did not produce the expected backend folder: $backendDistDir"
    }

    New-Item -ItemType Directory -Force -Path $electronBackendRoot | Out-Null
    if (Test-Path $electronBackendDir) {
        Remove-Item $electronBackendDir -Recurse -Force
    }

    Copy-Item $backendDistDir $electronBackendDir -Recurse -Force
    Write-Host "Backend copied to $electronBackendDir"
} finally {
    Pop-Location
}

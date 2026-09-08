$ErrorActionPreference = 'Stop'

$venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $venvPython)) {
    python -m venv (Join-Path $PSScriptRoot '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Unable to create the Python environment.' }
}

& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'Unable to upgrade pip.' }
& $venvPython -m pip install -e "$PSScriptRoot[build]"
if ($LASTEXITCODE -ne 0) { throw 'Unable to install build dependencies.' }

$ffmpeg = (Get-Command ffmpeg -ErrorAction Stop).Source
$ffprobe = (Get-Command ffprobe -ErrorAction Stop).Source
& $venvPython -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onedir `
    --name AutoVideoStitch `
    --collect-all transformers `
    --add-binary "${ffmpeg};ffmpeg" `
    --add-binary "${ffprobe};ffmpeg" `
    --paths (Join-Path $PSScriptRoot 'src') `
    (Join-Path $PSScriptRoot 'launcher.py')
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed.' }

Write-Host "Built: $PSScriptRoot\dist\AutoVideoStitch\AutoVideoStitch.exe"
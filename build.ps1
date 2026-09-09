param(
    [switch]$OnlineResources
)

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
$distributionRoot = if ($OnlineResources) { 'dist-online' } else { 'dist' }
$pyInstallerArguments = @(
    '-m', 'PyInstaller',
    '--noconfirm',
    '--clean',
    '--windowed',
    '--onedir',
    '--name', 'AutoVideoStitch',
    '--distpath', (Join-Path $PSScriptRoot $distributionRoot),
    '--runtime-hook', (Join-Path $PSScriptRoot 'pyi_runtime_dlls.py'),
    '--add-binary', "${ffmpeg};ffmpeg",
    '--add-binary', "${ffprobe};ffmpeg"
)

if ($OnlineResources) {
    $pyInstallerArguments += @('--add-data', "$(Join-Path $PSScriptRoot 'online-model-download.flag');.")
} else {
    $modelDirectory = Join-Path $PSScriptRoot 'build\models\openai-clip-vit-base-patch32'
    Remove-Item $modelDirectory -Recurse -Force -ErrorAction SilentlyContinue
    $downloadModel = "from huggingface_hub import snapshot_download; import sys; snapshot_download(repo_id='openai/clip-vit-base-patch32', local_dir=sys.argv[1], allow_patterns=['*.json', '*.txt', 'pytorch_model.bin'])"
    & $venvPython -c $downloadModel $modelDirectory
    if ($LASTEXITCODE -ne 0) { throw 'Unable to download the scene recognition model for bundling.' }
    $pyInstallerArguments += @('--add-data', "${modelDirectory};models/openai-clip-vit-base-patch32")
}

$pyInstallerArguments += @('--paths', (Join-Path $PSScriptRoot 'src'), (Join-Path $PSScriptRoot 'launcher.py'))
& $venvPython @pyInstallerArguments
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed.' }

Write-Host "Built: $PSScriptRoot\$distributionRoot\AutoVideoStitch\AutoVideoStitch.exe"
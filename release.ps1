param(
    [string]$Version = '1.0.2',
    [switch]$SkipBuild,
    [switch]$OnlineInstaller
)

$ErrorActionPreference = 'Stop'
$releaseDirectory = Join-Path $PSScriptRoot 'release'
$distributionRoot = if ($OnlineInstaller) { 'dist-online' } else { 'dist' }
$distribution = Join-Path $PSScriptRoot "$distributionRoot\AutoVideoStitch"
$innoCompiler = Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'

if (-not $SkipBuild) {
    & (Join-Path $PSScriptRoot 'build.ps1') -OnlineResources:$OnlineInstaller
    if ($LASTEXITCODE -ne 0) { throw 'Application build failed.' }
}
$requiredFiles = @(
    'AutoVideoStitch.exe',
    '_internal\ffmpeg\ffmpeg.exe',
    '_internal\ffmpeg\ffprobe.exe',
    '_internal\msvcp140.dll',
    '_internal\vcruntime140.dll',
    '_internal\vcruntime140_1.dll',
    '_internal\torch\lib\c10.dll',
    '_internal\torch\lib\libiomp5md.dll',
    '_internal\torch\lib\libiompstubs5md.dll',
    '_internal\torch\lib\shm.dll',
    '_internal\torch\lib\torch.dll',
    '_internal\torch\lib\torch_cpu.dll',
    '_internal\torch\lib\torch_global_deps.dll',
    '_internal\torch\lib\torch_python.dll',
    '_internal\torch\lib\uv.dll'
)
if ($OnlineInstaller) {
    $requiredFiles += '_internal\online-model-download.flag'
} else {
    $requiredFiles += @(
        '_internal\models\openai-clip-vit-base-patch32\config.json',
        '_internal\models\openai-clip-vit-base-patch32\preprocessor_config.json',
        '_internal\models\openai-clip-vit-base-patch32\tokenizer_config.json',
        '_internal\models\openai-clip-vit-base-patch32\vocab.json',
        '_internal\models\openai-clip-vit-base-patch32\merges.txt'
    )
}
foreach ($requiredFile in $requiredFiles) {
    if (-not (Test-Path (Join-Path $distribution $requiredFile))) {
        throw "The application distribution is missing $requiredFile. Run build.ps1 first."
    }
}
if (-not $OnlineInstaller) {
    $modelDirectory = Join-Path $distribution '_internal\models\openai-clip-vit-base-patch32'
    if (-not ((Test-Path (Join-Path $modelDirectory 'model.safetensors')) -or (Test-Path (Join-Path $modelDirectory 'pytorch_model.bin')))) {
        throw 'The application distribution is missing the scene recognition model weights. Run build.ps1 first.'
    }
}
if (-not (Test-Path $innoCompiler)) {
    throw 'Inno Setup 6 is required. Install it with: winget install JRSoftware.InnoSetup'
}

New-Item -ItemType Directory -Force -Path $releaseDirectory | Out-Null
$portableArchive = Join-Path $releaseDirectory "AutoVideoStitch-Portable-$Version.zip"
$checksumFile = Join-Path $releaseDirectory "AutoVideoStitch-$Version-SHA256.txt"
$installerBaseName = if ($OnlineInstaller) { "AutoVideoStitch-Online-Setup-$Version" } else { "AutoVideoStitch-Setup-$Version" }
$installer = Join-Path $releaseDirectory "$installerBaseName.exe"
Remove-Item $installer, $checksumFile -Force -ErrorAction SilentlyContinue

if (-not $OnlineInstaller) {
    Remove-Item $portableArchive -Force -ErrorAction SilentlyContinue
    Compress-Archive -Path $distribution -DestinationPath $portableArchive -CompressionLevel Optimal
}
& $innoCompiler "/DMyAppVersion=$Version" "/DMyDistributionDir=$distribution" "/DMyOutputBaseFilename=$installerBaseName" (Join-Path $PSScriptRoot 'installer.iss')
if ($LASTEXITCODE -ne 0) { throw 'Installer compilation failed.' }

$artifactNames = @(
    "AutoVideoStitch-Setup-$Version.exe",
    "AutoVideoStitch-Online-Setup-$Version.exe",
    "AutoVideoStitch-Portable-$Version.zip"
)
$artifacts = $artifactNames | ForEach-Object { Join-Path $releaseDirectory $_ } | Where-Object { Test-Path $_ }
$hashes = Get-FileHash -Algorithm SHA256 $artifacts
$hashes | ForEach-Object { "$($_.Hash)  $([IO.Path]::GetFileName($_.Path))" } | Set-Content $checksumFile -Encoding ascii

Write-Host "Installer: $installer"
if (-not $OnlineInstaller) { Write-Host "Portable:  $portableArchive" }
Write-Host "Checksums: $checksumFile"
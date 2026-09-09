param(
    [string]$Version = '1.0.3',
    [switch]$SkipBuild,
    [switch]$OnlineInstaller
)

$ErrorActionPreference = 'Stop'
$releaseDirectory = Join-Path $PSScriptRoot 'release'
$distributionRoot = if ($OnlineInstaller) { 'dist-online' } else { 'dist' }
$distribution = Join-Path $PSScriptRoot "$distributionRoot\AutoVideoStitch"
$innoCompiler = Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'
$prerequisiteDirectory = Join-Path $PSScriptRoot 'build\prerequisites'
$prerequisitePackages = @(
    [pscustomobject]@{ Id = 'Microsoft.VCRedist.2015+.x64'; FileName = 'VC_redist.2015plus.x64.exe' },
    [pscustomobject]@{ Id = 'Microsoft.VCRedist.2015+.x86'; FileName = 'VC_redist.2015plus.x86.exe' },
    [pscustomobject]@{ Id = 'Microsoft.VCRedist.2013.x64'; FileName = 'VC_redist.2013.x64.exe' },
    [pscustomobject]@{ Id = 'Microsoft.VCRedist.2013.x86'; FileName = 'VC_redist.2013.x86.exe' }
)

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
$runtimeReport = Join-Path $env:TEMP "AutoVideoStitch-runtime-$([guid]::NewGuid().ToString('N')).txt"
try {
    $runtimeCheck = Start-Process `
        -FilePath (Join-Path $distribution 'AutoVideoStitch.exe') `
        -ArgumentList @('--verify-runtime', $runtimeReport) `
        -Wait `
        -PassThru
    if ($runtimeCheck.ExitCode -ne 0) {
        $runtimeDetails = if (Test-Path $runtimeReport) { Get-Content $runtimeReport -Raw } else { 'No diagnostic report was created.' }
        throw "The packaged Torch runtime failed to load:`n$runtimeDetails"
    }
} finally {
    Remove-Item $runtimeReport -Force -ErrorAction SilentlyContinue
}
if (-not (Test-Path $innoCompiler)) {
    throw 'Inno Setup 6 is required. Install it with: winget install JRSoftware.InnoSetup'
}
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw 'WinGet is required to download the Microsoft Visual C++ prerequisites.'
}

Remove-Item $prerequisiteDirectory -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $prerequisiteDirectory | Out-Null
foreach ($package in $prerequisitePackages) {
    $packageDirectory = Join-Path $prerequisiteDirectory $package.Id
    New-Item -ItemType Directory -Force -Path $packageDirectory | Out-Null
    & winget download `
        --exact `
        --id $package.Id `
        --download-directory $packageDirectory `
        --accept-source-agreements `
        --accept-package-agreements `
        --disable-interactivity
    if ($LASTEXITCODE -ne 0) { throw "Unable to download prerequisite $($package.Id)." }
    $downloads = @(Get-ChildItem $packageDirectory -Filter '*.exe' -File -Recurse)
    if ($downloads.Count -ne 1) { throw "Expected one executable for prerequisite $($package.Id), found $($downloads.Count)." }
    Move-Item $downloads[0].FullName (Join-Path $prerequisiteDirectory $package.FileName)
    Remove-Item $packageDirectory -Recurse -Force
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
& $innoCompiler "/DMyAppVersion=$Version" "/DMyDistributionDir=$distribution" "/DMyPrerequisiteDir=$prerequisiteDirectory" "/DMyOutputBaseFilename=$installerBaseName" (Join-Path $PSScriptRoot 'installer.iss')
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
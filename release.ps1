param(
    [string]$Version = '1.0.1',
    [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'
$releaseDirectory = Join-Path $PSScriptRoot 'release'
$distribution = Join-Path $PSScriptRoot 'dist\AutoVideoStitch'
$innoCompiler = Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'

if (-not $SkipBuild) {
    & (Join-Path $PSScriptRoot 'build.ps1')
    if ($LASTEXITCODE -ne 0) { throw 'Application build failed.' }
}
if (-not (Test-Path (Join-Path $distribution 'AutoVideoStitch.exe'))) {
    throw 'The application distribution is missing. Run build.ps1 first.'
}
if (-not (Test-Path $innoCompiler)) {
    throw 'Inno Setup 6 is required. Install it with: winget install JRSoftware.InnoSetup'
}

New-Item -ItemType Directory -Force -Path $releaseDirectory | Out-Null
$portableArchive = Join-Path $releaseDirectory "AutoVideoStitch-Portable-$Version.zip"
$checksumFile = Join-Path $releaseDirectory "AutoVideoStitch-$Version-SHA256.txt"
Remove-Item $portableArchive, $checksumFile -Force -ErrorAction SilentlyContinue

Compress-Archive -Path $distribution -DestinationPath $portableArchive -CompressionLevel Optimal
& $innoCompiler "/DMyAppVersion=$Version" (Join-Path $PSScriptRoot 'installer.iss')
if ($LASTEXITCODE -ne 0) { throw 'Installer compilation failed.' }

$installer = Join-Path $releaseDirectory "AutoVideoStitch-Setup-$Version.exe"
$hashes = Get-FileHash -Algorithm SHA256 $installer, $portableArchive
$hashes | ForEach-Object { "$($_.Hash)  $([IO.Path]::GetFileName($_.Path))" } | Set-Content $checksumFile -Encoding ascii

Write-Host "Installer: $installer"
Write-Host "Portable:  $portableArchive"
Write-Host "Checksums: $checksumFile"
#define MyAppName "Auto Video Stitch"
#ifndef MyAppVersion
#define MyAppVersion "1.0.2"
#endif
#ifndef MyDistributionDir
#define MyDistributionDir "dist\AutoVideoStitch"
#endif
#ifndef MyOutputBaseFilename
#define MyOutputBaseFilename "AutoVideoStitch-Setup-" + MyAppVersion
#endif
#define MyAppPublisher "jwgmpi-wolff"
#define MyAppExeName "AutoVideoStitch.exe"

[Setup]
AppId={{A2201FE8-DDE9-40A2-BD9A-D884EE096098}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\Auto Video Stitch
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=release
OutputBaseFilename={#MyOutputBaseFilename}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
CloseApplications=yes
RestartApplications=no

[Files]
Source: "{#MyDistributionDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
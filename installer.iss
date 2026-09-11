#define MyAppName "Auto Video Stitch"
#ifndef MyAppVersion
#define MyAppVersion "1.0.3"
#endif
#ifndef MyDistributionDir
#define MyDistributionDir "dist\AutoVideoStitch"
#endif
#ifndef MyOutputBaseFilename
#define MyOutputBaseFilename "AutoVideoStitch-Setup-" + MyAppVersion
#endif
#ifndef MyPrerequisiteDir
#define MyPrerequisiteDir "build\prerequisites"
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
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
CloseApplications=yes
RestartApplications=no

[Files]
Source: "{#MyDistributionDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MyPrerequisiteDir}\VC_redist.2015plus.x64.exe"; Flags: dontcopy
Source: "{#MyPrerequisiteDir}\VC_redist.2015plus.x86.exe"; Flags: dontcopy
Source: "{#MyPrerequisiteDir}\VC_redist.2013.x64.exe"; Flags: dontcopy
Source: "{#MyPrerequisiteDir}\VC_redist.2013.x86.exe"; Flags: dontcopy

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
function InstallPrerequisite(const FileName, DisplayName: String; var NeedsRestart: Boolean): String;
var
	ResultCode: Integer;
begin
	Result := '';
	ExtractTemporaryFile(FileName);
	WizardForm.StatusLabel.Caption := 'Installing ' + DisplayName + '...';
	if not Exec(ExpandConstant('{tmp}\' + FileName), '/install /quiet /norestart', '', SW_HIDE,
		ewWaitUntilTerminated, ResultCode) then
	begin
		Result := 'Unable to start ' + DisplayName + '.';
		Exit;
	end;
	if ResultCode = 3010 then
		NeedsRestart := True
	else if (ResultCode <> 0) and (ResultCode <> 1638) then
		Result := DisplayName + ' installation failed with exit code ' + IntToStr(ResultCode) + '.';
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
	Result := InstallPrerequisite('VC_redist.2015plus.x64.exe',
		'Microsoft Visual C++ 2015-2022 Redistributable (x64)', NeedsRestart);
	if Result <> '' then Exit;
	Result := InstallPrerequisite('VC_redist.2015plus.x86.exe',
		'Microsoft Visual C++ 2015-2022 Redistributable (x86)', NeedsRestart);
	if Result <> '' then Exit;
	Result := InstallPrerequisite('VC_redist.2013.x64.exe',
		'Microsoft Visual C++ 2013 Redistributable (x64)', NeedsRestart);
	if Result <> '' then Exit;
	Result := InstallPrerequisite('VC_redist.2013.x86.exe',
		'Microsoft Visual C++ 2013 Redistributable (x86)', NeedsRestart);
end;
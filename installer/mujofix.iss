; Inno Setup installer (Windows): kompajlirati s ISTOPROK 6.
; Bundluje: dist\MujoFix\* + pinovanu OpenCode kopiju iz build\opencode\.
; OpenCode verzija + SHA-256: installer/OPENCODE_PIN.txt (rucno odrzavano,
; provjereno prije svakog release-a). Netestirano na Win.

#define MyAppName "MujoFix"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "MujoFix contributors"
#define MyAppURL "https://github.com/xnet-ba/mujofix"

[Setup]
AppId={{3F4A1B2C-9D8E-4F7A-A6B5-C4D3E2F1A0B9}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={localappdata}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=Output
OutputBaseFilename=MujoFix-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
UninstallDisplayName={#MyAppName}
; BEZ potpisa: ne tvrdimo da je build potpisan (SmartScreen ce upozoriti)

[Languages]
Name: "bosnian"; MessagesFile: "compiler:Languages\Bosnian.isl"

[Tasks]
Name: "desktopicon"; Description: "Ikona na desktopu"; Flags: unchecked

[Files]
Source: "dist\MujoFix\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "build\opencode\*"; DestDir: "{app}\opencode"; Flags: ignoreversion recursesubdirs
Source: "installer\OPENCODE_PIN.txt"; DestDir: "{app}\opencode"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\MujoFix.exe"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\MujoFix.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\MujoFix.exe"; Description: "Pokreni MujoFix"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; deinstalacija uklanja OpenCode kopiju i podatke aplikacije
Type: filesandordirs; Name: "{app}\opencode"
Type: filesandordirs; Name: "{localappdata}\{#MyAppName}"

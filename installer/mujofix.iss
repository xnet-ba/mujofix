; Inno Setup installer (Windows): kompajlirati s ISTOPROK 6.
; Bundluje sve iz dist\MujoFix\ (ukljucujuci opencode\ koji CI ubaci u dist).
; OpenCode verzija + SHA-256: installer/OPENCODE_PIN.txt (rucno odrzavano,
; provjereno prije svakog release-a).
; Verzija se moze ubaciti s /DMyAppVersion=<ver> (CI je cita iz CHANGELOG.md).
; Kompajlira se u CI (job installer-windows) na svakom push-u.

#define MyAppName "MujoFix"
#ifndef MyAppVersion
#define MyAppVersion "0.4.0"
#endif
#define MyAppPublisher "MujoFix contributors"
#define MyAppURL "https://github.com/xnet-ba/mujofix"

[Setup]
; SourceDir = repo root. Inno inace trazi Source putanje relativno na folder
; ovog .iss-a, pa bi se "dist\MujoFix\*" trazio u installer\dist\MujoFix\*.
SourceDir=..
AppId={{3F4A1B2C-9D8E-4F7A-A6B5-C4D3E2F1A0B9}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={localappdata}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=installer\Output
OutputBaseFilename=MujoFix-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
UninstallDisplayName={#MyAppName}
; Ikona setup exe-a. NAPOMENA: Inno rjesava SetupIconFile relativno na
; SourceDir (repo root), ne na folder .iss-a — CI je pao na '..\assets\...'.
SetupIconFile=assets\mujofix.ico
; BEZ potpisa: ne tvrdimo da je build potpisan (SmartScreen ce upozoriti)

; Inno Setup 6.7.1 ne isporucuje Bosnian.isl, pa je installer na engleskom
; (Default.isl). Ako se doda installer\Languages\Bosnian.isl, vrati [Languages]
; sekciju:  Name: "bosnian"; MessagesFile: "compiler:Languages\Bosnian.isl"

[Tasks]
Name: "desktopicon"; Description: "Ikona na desktopu"; Flags: unchecked

[Files]
Source: "dist\MujoFix\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
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

; Script Inno Setup pour MT5 Set Editor
; Génère un installateur Windows classique (installation dans Program Files,
; raccourcis Menu Démarrer / Bureau, désinstallation propre via
; "Applications et fonctionnalités", association optionnelle des .set).
;
; Prérequis : construire dist\MT5SetEditor.exe au préalable (PyInstaller) :
;   python -m PyInstaller --noconsole --onefile --name "MT5SetEditor" main.py
;
; Compilation :
;   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
; Le setup généré se trouve dans le dossier "installer_output".

#define MyAppName "MT5 Set Editor"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "MT5 Set Editor"
#define MyAppExeName "MT5SetEditor.exe"

[Setup]
AppId={{9C6E6E2A-9E2F-4C4B-8C7B-3F2D2C6C7A11}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=MT5SetEditor_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le Bureau"; GroupDescription: "Raccourcis :"
Name: "assocset"; Description: "Ouvrir les fichiers .set avec {#MyAppName} (double-clic)"; GroupDescription: "Association de fichiers :"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Désinstaller {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
Root: HKA; Subkey: "Software\Classes\.set\OpenWithProgids"; ValueType: string; ValueName: "MT5SetEditor.set"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assocset
Root: HKA; Subkey: "Software\Classes\MT5SetEditor.set"; ValueType: string; ValueName: ""; ValueData: "Fichier de paramètres MT5"; Flags: uninsdeletekey; Tasks: assocset
Root: HKA; Subkey: "Software\Classes\MT5SetEditor.set\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"; Tasks: assocset
Root: HKA; Subkey: "Software\Classes\MT5SetEditor.set\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: assocset

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Lancer {#MyAppName}"; Flags: nowait postinstall skipifsilent

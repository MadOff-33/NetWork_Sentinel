; ============================================================
;  Network Sentinel - Installeur client (Inno Setup)
; ============================================================
;  Compilation :
;    1. Installer Inno Setup (https://jrsoftware.org/isdl.php)
;    2. Ouvrir ce fichier dans Inno Setup, ou :
;         "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\installer.iss
;    3. Le setup est genere dans installer\output\
;
;  Prerequis : avoir construit l'exe au prealable
;         pyinstaller NetworkSentinel.spec   (-> dist\NetworkSentinel.exe)
;
;  Installation SANS droits admin (dossier utilisateur) : le client ecrit
;  sa config et ses logs a cote de lui, donc pas dans Program Files.
; ============================================================

#define AppName "Network Sentinel"
#define AppVersion "2.0"
#define AppPublisher "Michael Introligator"
#define AppExe "NetworkSentinel.exe"

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\Network Sentinel
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=output
OutputBaseFilename=NetworkSentinel-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; Icone de l'appli comme icone du setup (facultatif)
; SetupIconFile=..\assets\icon.ico

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le Bureau"; GroupDescription: "Raccourcis :"

[Files]
Source: "..\dist\NetworkSentinel.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\docs\GUIDE_UTILISATION.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"
Name: "{group}\Guide d'utilisation"; Filename: "{app}\GUIDE_UTILISATION.md"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "Lancer Network Sentinel"; Flags: nowait postinstall skipifsilent

[Code]
var
  ConfigPage: TInputQueryWizardPage;

procedure InitializeWizard;
begin
  { Page personnalisee : connexion au NAS }
  ConfigPage := CreateInputQueryPage(wpSelectDir,
    'Connexion au serveur', 'Où se trouve le serveur Network Sentinel ?',
    'Renseignez l''adresse IP de votre NAS et le token d''accès ' +
    '(fournis par votre installateur). Vous pourrez les modifier plus ' +
    'tard dans l''onglet Paramètres.');
  ConfigPage.Add('Adresse IP du NAS :', False);
  ConfigPage.Add('Token API (laisser vide si non utilisé) :', False);
  ConfigPage.Values[0] := '192.168.1.100';
  ConfigPage.Values[1] := '';
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Json: String;
begin
  if CurStep = ssPostInstall then
  begin
    { Ecrit client_config.json a cote de l'exe }
    Json := '{' + #13#10 +
      '    "nas_ip": "' + ConfigPage.Values[0] + '",' + #13#10 +
      '    "api_token": "' + ConfigPage.Values[1] + '"' + #13#10 +
      '}';
    SaveStringToFile(ExpandConstant('{app}\client_config.json'), Json, False);
  end;
end;

[UninstallDelete]
; Nettoie les fichiers generes par l'appli a la desinstallation
Type: files; Name: "{app}\client_config.json"
Type: filesandordirs; Name: "{app}\logs"

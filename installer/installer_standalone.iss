; ============================================================
;  Network Sentinel - Édition AUTONOME (standalone) - Inno Setup
; ============================================================
;  Version tout-en-un : scanne le réseau depuis le PC, sans NAS.
;  Nécessite Npcap (pilote de capture) et les droits administrateur.
;
;  Compilation :
;    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\installer_standalone.iss
;    -> setup dans installer\output\
;
;  Prérequis : pyinstaller NetworkSentinelStandalone.spec
;              (-> dist\NetworkSentinelStandalone.exe)
;
;  Npcap : placez éventuellement l'installeur officiel dans
;          installer\redist\npcap-installer.exe pour qu'il soit proposé
;          automatiquement (téléchargeable sur https://npcap.com).
; ============================================================

#define AppName "Network Sentinel Autonome"
#define AppVersion "2.0"
#define AppPublisher "Michael Introligator"
#define AppExe "NetworkSentinelStandalone.exe"

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\Network Sentinel Autonome
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
; Le scan ARP exige les droits admin -> installation machine
PrivilegesRequired=admin
OutputDir=output
OutputBaseFilename=NetworkSentinel-Autonome-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le Bureau"; GroupDescription: "Raccourcis :"

[Files]
Source: "..\dist\NetworkSentinelStandalone.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\docs\GUIDE_UTILISATION.md"; DestDir: "{app}"; Flags: ignoreversion isreadme
; Npcap (optionnel) : inclus seulement si présent dans redist\
Source: "redist\npcap-installer.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall skipifsourcedoesntexist

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"
Name: "{group}\Guide d'utilisation"; Filename: "{app}\GUIDE_UTILISATION.md"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
; Installe Npcap si son installeur a été fourni et qu'il n'est pas déjà présent
Filename: "{tmp}\npcap-installer.exe"; Parameters: "/S"; StatusMsg: "Installation de Npcap (pilote réseau)..."; Flags: waituntilterminated skipifdoesntexist; Check: NpcapManquant
Filename: "{app}\{#AppExe}"; Description: "Lancer Network Sentinel Autonome"; Flags: nowait postinstall skipifsilent

[Code]
function NpcapManquant: Boolean;
begin
  { Npcap est présent si son service/DLL existe }
  Result := not (FileExists(ExpandConstant('{sys}\Npcap\wpcap.dll'))
             or FileExists(ExpandConstant('{sys}\wpcap.dll')));
end;

procedure InitializeWizard;
begin
  if NpcapManquant then
    MsgBox('Cette application a besoin de « Npcap » pour analyser le réseau.'
      + #13#10 + #13#10
      + 'S''il n''est pas installé automatiquement, téléchargez-le sur '
      + 'https://npcap.com puis relancez l''application.',
      mbInformation, MB_OK);
end;

[UninstallDelete]
Type: files; Name: "{app}\client_config.json"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\data"

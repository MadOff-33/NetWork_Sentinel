@echo off
rem Lanceur du client Network Sentinel (sans fenetre console).
rem %~dp0 = dossier du .bat -> fonctionne meme si le projet est deplace.
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" main.py
) else (
    rem Pas de venv : tente le Python du systeme
    start "" pythonw main.py
)

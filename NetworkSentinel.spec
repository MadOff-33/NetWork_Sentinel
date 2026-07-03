# -*- mode: python ; coding: utf-8 -*-
# Build du CLIENT Network Sentinel (pilote le serveur NAS).
# Le client ne scanne PAS lui-meme -> ni scapy ni Npcap ni droits admin.
# Les exclusions ci-dessous retirent tout ce que customtkinter/matplotlib/
# pandas/requests n'utilisent pas, pour un exe le plus leger possible.

from PyInstaller.utils.hooks import collect_submodules

# Modules NON necessaires au client (le gros du poids evite)
EXCLUDES = [
    # Reseau bas niveau : c'est le serveur NAS qui scanne, pas le client
    'scapy', 'ping3',
    # Frameworks GUI concurrents embarques par erreur
    'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'wx',
    # Stack scientifique non utilisee
    'scipy', 'sympy', 'IPython', 'jupyter', 'notebook', 'nbconvert',
    # Outils de dev
    'pytest', 'ruff', 'pyinstaller', 'setuptools._vendor',
    # Backends matplotlib inutiles (on ne garde que TkAgg)
    'matplotlib.backends._backend_gtk', 'matplotlib.backends.backend_qt5agg',
    'matplotlib.backends.backend_qtagg', 'matplotlib.backends.backend_wxagg',
    'matplotlib.backends.backend_webagg', 'matplotlib.tests', 'numpy.tests',
    'pandas.tests',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('src', 'src')],
    hiddenimports=['winshell', 'win32com.client'] + collect_submodules('customtkinter'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='NetworkSentinel',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

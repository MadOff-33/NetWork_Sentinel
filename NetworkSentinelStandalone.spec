# -*- mode: python ; coding: utf-8 -*-
# Build de l'EDITION AUTONOME (standalone) : serveur embarque + GUI.
# Contrairement au client, elle scanne le reseau elle-meme -> Scapy inclus
# (necessite Npcap installe + droits admin a l'execution).

from PyInstaller.utils.hooks import collect_submodules

hidden = (
    ['winshell', 'win32com.client']
    + collect_submodules('customtkinter')
    + collect_submodules('scapy')
    + ['server', 'server.server',
       'src.scanner', 'src.security', 'src.analyzer',
       'src.notifier', 'src.port_scanner', 'src.logger',
       'flask', 'ping3', 'pandas', 'matplotlib.backends.backend_tkagg']
)

# On garde les exclusions "poids mort" mais on NE retire PAS scapy/ping3/flask
EXCLUDES = [
    'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'wx',
    'scipy', 'sympy', 'IPython', 'jupyter', 'notebook', 'nbconvert',
    'pytest', 'ruff', 'pyinstaller',
    'matplotlib.backends.backend_qt5agg', 'matplotlib.backends.backend_qtagg',
    'matplotlib.backends.backend_wxagg', 'matplotlib.backends.backend_webagg',
    'matplotlib.tests', 'numpy.tests', 'pandas.tests',
]

a = Analysis(
    ['main_standalone.py'],
    pathex=[],
    binaries=[],
    datas=[('src', 'src'), ('server', 'server')],
    hiddenimports=hidden,
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
    name='NetworkSentinelStandalone',
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
    uac_admin=True,
)

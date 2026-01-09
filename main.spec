# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_submodules

project_root = os.path.abspath(os.path.dirname(__name__))

datas = [
    # Angular
    (
        os.path.join(project_root, "web", "dist", "cofmupy-gui"),
        os.path.join("web", "dist", "cofmupy-gui")
    ),

    # VERSION dans son sous-répertoire exact
    (
        os.path.join(project_root, "cofmupy", "VERSION"),
        os.path.join("cofmupy")
    ),
]

hiddenimports = (
    collect_submodules("eventlet") +
    collect_submodules("engineio") +
    collect_submodules("socketio")
)

block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='cofmupy-dist',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
)


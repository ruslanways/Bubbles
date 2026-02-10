# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("img/logo.gif", "img"),
        ("sound/intro.mp3", "sound"),
        ("sound/stage1.mp3", "sound"),
        ("sound/stage2.mp3", "sound"),
        ("sound/stage3.mp3", "sound"),
        ("sound/hit.mp3", "sound"),
        ("sound/fail.mp3", "sound"),
        ("sound/win.wav", "sound"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="bubbles",
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

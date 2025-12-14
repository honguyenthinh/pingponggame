# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['pingpong.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\admin\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\mediapipe', 'mediapipe')],
    hiddenimports=['cv2'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='pingpong',
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
    icon=['pingpong.ico'],
)

# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['gui_main.py'],
    pathex=['src'],
    binaries=[],
    datas=[('resources', 'resources'), ('templates', 'templates'), ('src\\s2ibispy\\data', 's2ibispy\\data')],
    hiddenimports=['s2ibispy.cli', 's2ibispy.loader', 's2ibispy.s2ianaly', 's2ibispy.s2ioutput', 's2ibispy.s2ispice', 's2ibispy.models', 's2ibispy.schema', 's2ibispy.s2i_constants', 's2ibispy.correlation', 's2ibispy.s2i_to_yaml'],
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
    name='s2ibispy',
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
    icon=['resources\\icons\\s2ibispy.ico'],
)

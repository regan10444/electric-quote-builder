# build.spec — PyInstaller spec for an Electrical Quote Builder
# Run: pyinstaller build.spec

import os
block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[os.path.abspath('.')],
    binaries=[],
    datas=[
        ('data', 'data'),       # bundle any existing data files
    ],
    hiddenimports=[
        'customtkinter',
        'reportlab',
        'reportlab.graphics',
        'reportlab.platypus',
        'reportlab.lib',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ElectricalQuoteBuilder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # no console window — GUI only
    icon=None,              # add an .ico file path here if you have one
)

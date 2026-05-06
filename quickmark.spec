# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Quickmark SSG.
Build: pyinstaller quickmark.spec
"""
import os
import sys

block_cipher = None

PROJECT_ROOT = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('template.html', '.'),
        ('content', 'content'),
        ('static', 'static'),
        ('src', 'src'),
    ],
    hiddenimports=[
        'httpx',
        'flet',
        'flet.core',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'unittest',
        'email',
        'xml',
        'pydoc',
    ],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='quickmark',
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

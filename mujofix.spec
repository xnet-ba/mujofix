# PyInstaller build (Windows):  python -m PyInstaller mujofix.spec
# Rezultat: dist/MujoFix/ s MujoFix.exe (GUI, bez konzole) + MujoFixCLI.exe.
# Format provjeren lokalnim Linux buildom (PyInstaller 6.22); Win exe iz CI-ja.
# Verzija se cita iz CHANGELOG.md (vrh, "## [x.y.z]").

import re

with open("CHANGELOG.md", encoding="utf-8") as handle:
    match = re.search(r"## \[(\d+\.\d+\.\d+)\]", handle.read())
VERSION = match.group(1) if match else "0.0.0"

common = dict(
    pathex=[],
    binaries=[],
    datas=[("mujofix/i18n", "mujofix/i18n")],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
)

gui_a = Analysis(["mujofix/ui/main_window.py"], **common)
gui_pyz = PYZ(gui_a.pure, gui_a.zipped_data)
gui_exe = EXE(
    gui_pyz,
    gui_a.scripts,
    [],
    exclude_binaries=True,
    name="MujoFix",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="NONE",
)

cli_a = Analysis(["mujofix/cli.py"], **common)
cli_pyz = PYZ(cli_a.pure, cli_a.zipped_data)
cli_exe = EXE(
    cli_pyz,
    cli_a.scripts,
    [],
    exclude_binaries=True,
    name="MujoFixCLI",
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
    icon="NONE",
)

coll = COLLECT(
    gui_exe,
    cli_exe,
    gui_a.binaries,
    gui_a.datas,
    cli_a.binaries,
    cli_a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="MujoFix",
)

# PyInstaller build (Windows):  python -m PyInstaller mujofix.spec
# Rezultat: dist/MujoFix.exe (GUI, bez konzole) + dist/MujoFixCLI.exe (CLI).
# Verzija se cita iz CHANGELOG.md (vrh, "## [x.y.z]"). Netestirano na Win.

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
    noarchive=False,
)

gui_analysis = Analysis(
    ["mujofix/ui/main_window.py"], **common,
    cipher=None, noarchive=False)
gui_exe = EXE(
    gui_analysis, name="MujoFix", debug=False,
    bootloader_ignore_signals=False, strip=False, upx=True,
    console=False, icon=None, version=None)

cli_analysis = Analysis(
    ["mujofix/cli.py"], **common,
    cipher=None, noarchive=False)
cli_exe = EXE(
    cli_analysis, name="MujoFixCLI", debug=False,
    bootloader_ignore_signals=False, strip=False, upx=True,
    console=True, icon=None, version=None)

coll = COLLECT(
    gui_exe, cli_exe, gui_analysis, cli_analysis,
    strip=False, upx=True, name="MujoFix")

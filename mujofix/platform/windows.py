"""Platform sloj: Windows detekcija + wrapperi (samo stdlib, bez pywin32).

Pravilo: svaka funkcija na nepodrzanoj platformi dize NotSupported umjesto da
lazira podatke. Scanneri to hvataju i graceful se iskljucuju.
Cijeli modul je mockabilan pa testovi prolaze i na Linuxu.
"""

from __future__ import annotations

import os
import sys

WIN10_22H2_BUILD = 19045


class NotSupported(Exception):
    """Platforma/verzija ne podrzava trazenu operaciju."""


def is_windows() -> bool:
    return sys.platform == "win32"


def version() -> tuple[int, int, int] | None:
    """(major, minor, build) ili None ako nije Windows. Netestirano na Win10/11."""
    if not is_windows():
        return None
    v = sys.getwindowsversion()
    return (v.major, v.minor, v.build)


def is_supported() -> bool:
    """Win10 22H2+ ili Win11. ARM64: netestirano, tretira se kao podrzano."""
    ver = version()
    if ver is None:
        return False
    major, _minor, build = ver
    if major > 10:
        return True
    return major == 10 and build >= WIN10_22H2_BUILD


def read_reg_values(hive: str, path: str) -> dict[str, str]:
    """Vrati {ime: vrijednost} potkljuca. Hive: 'HKCU' ili 'HKLM'."""
    if not is_windows():
        raise NotSupported("registry postoji samo na Windowsu")
    import winreg

    hives = {"HKCU": winreg.HKEY_CURRENT_USER, "HKLM": winreg.HKEY_LOCAL_MACHINE}
    if hive not in hives:
        raise ValueError(f"nepoznat hive: {hive}")
    out: dict[str, str] = {}
    try:
        with winreg.OpenKey(hives[hive], path) as key:
            _index = 0
            while True:
                try:
                    name, value, _kind = winreg.EnumValue(key, _index)
                except OSError:
                    break
                out[str(name)] = str(value)
                _index += 1
    except FileNotFoundError:
        pass
    return out


def startup_folders() -> list[str]:
    """Startup folderi (korisnicki + zajednicki); prazno ako nisu dostupni."""
    folders: list[str] = []
    if is_windows():
        appdata = os.environ.get("APPDATA", "")
        programdata = os.environ.get("PROGRAMDATA", "")
        if appdata:
            folders.append(
                os.path.join(
                    appdata, "Microsoft", "Windows", "Start Menu",
                    "Programs", "Startup",
                )
            )
        if programdata:
            folders.append(
                os.path.join(
                    programdata, "Microsoft", "Windows", "Start Menu",
                    "Programs", "Startup",
                )
            )
    return [f for f in folders if os.path.isdir(f)]


def list_folder_entries(folder: str) -> list[str]:
    """Imena stavki u folderu (samo stdlib, bez pracenja .lnk meta)."""
    try:
        return sorted(
            entry.name for entry in os.scandir(folder) if entry.is_file()
        )
    except OSError:
        return []

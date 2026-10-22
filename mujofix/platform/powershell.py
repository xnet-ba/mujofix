"""PowerShell kao izvor strukturiranih podataka (Windows-only, samo citanje).

Zasto PowerShell + JSON: `schtasks`/`sc` ispisi su LOKALIZOVANI (na bosanskom
Windowsu drugaciji), pa je parsiranje krhko. PowerShell vrati objekte, a
`ConvertTo-Json` daje stabilan oblik nezavisan od jezika sistema.
"""

from __future__ import annotations

import json
import subprocess


def ps_json(command: str, timeout_s: int = 90) -> object:
    """Pokreni PowerShell komandu i vrati parsiran JSON izlaz.

    Dize RuntimeError ako komanda padne ili izlaz nije JSON (pozivaoci to
    hvataju i graceful preskacu — scanner nikad ne rusi cijeli SCAN).
    """
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
        capture_output=True, text=True, timeout=timeout_s)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip()[-200:])
    return json.loads(proc.stdout or "null")

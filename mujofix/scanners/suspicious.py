"""Sumnjivi procesi (samo Windows): autostart iz Temp/AppData + potpis.

Nikad ne tvrdi "virus" — samo "sumnjivo, razlozi: ...". Defender status se
cita (read-only), nikad se ne mijenja. Potpis: Get-AuthenticodeSignature.
"""

from __future__ import annotations

import json
import os
import subprocess

from mujofix.core.models import Finding
from mujofix.platform import windows
from mujofix.scanners.base import ScanContext, Scanner, register
from mujofix.scanners.startup import RUN_KEYS

_PS_PROCESS_CMD = "Get-Process | Select-Object Name,Id,Path | ConvertTo-Json"
MAX_SIG_CHECKS = 20


def _ps_json(command: str, timeout_s: int = 90) -> object:
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
        capture_output=True, text=True, timeout=timeout_s)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip()[-200:])
    return json.loads(proc.stdout or "null")


def _processes() -> list[dict]:
    data = _ps_json(_PS_PROCESS_CMD)
    return data if isinstance(data, list) else [data]


def _signature_status(path: str) -> str:
    try:
        data = _ps_json(
            f"Get-AuthenticodeSignature -FilePath '{path}' | "
            "Select-Object -ExpandProperty Status",
            timeout_s=30)
    except Exception:
        return "nepoznato"
    return str(data) if data else "nepoznato"


def _odd_locations() -> list[str]:
    locs = []
    for var in ("TEMP", "TMP"):
        value = os.environ.get(var, "")
        if value:
            locs.append(os.path.normcase(value))
    windir = os.environ.get("SystemRoot", r"C:\Windows")
    locs.append(os.path.normcase(os.path.join(windir, "Temp")))
    appdata = os.environ.get("LOCALAPPDATA", "")
    if appdata:
        locs.append(os.path.normcase(os.path.join(appdata, "Temp")))
    return locs


def _autostart_names() -> set[str]:
    names: set[str] = set()
    for hive, path in RUN_KEYS:
        try:
            values = windows.read_reg_values(hive, path)
        except windows.NotSupported:
            return set()
        for command in values.values():
            first = command.strip().strip('"').split()[0] if command.strip() \
                else ""
            base = os.path.basename(first).lower()
            if base:
                names.add(base)
    for folder in windows.startup_folders():
        for entry in windows.list_folder_entries(folder):
            names.add(entry.lower())
    return names


@register
class SuspiciousScanner(Scanner):
    name = "suspicious"

    def is_available(self) -> bool:
        return windows.is_windows()

    def unavailable_reason(self) -> str:
        return "lista procesa i potpisi citaju se samo na Windowsu"

    def _scan(self, ctx: ScanContext) -> list[Finding]:
        findings: list[Finding] = []
        try:
            processes = _processes()
        except (OSError, RuntimeError) as exc:
            raise RuntimeError(f"Get-Process nedostupan: {exc}")
        odd = _odd_locations()
        autostart = _autostart_names()

        suspects: list[dict] = []
        for proc in processes:
            path = proc.get("Path") or ""
            name = str(proc.get("Name", "?"))
            if not path:
                continue
            norm = os.path.normcase(path)
            reasons = []
            if any(norm.startswith(loc) for loc in odd):
                reasons.append("pokrenut iz privremenog foldera")
            exe = os.path.basename(norm)
            if exe in autostart and any(norm.startswith(loc) for loc in odd):
                reasons.append("autostart iz privremenog foldera")
            if reasons:
                suspects.append({"name": name, "pid": proc.get("Id"),
                                 "path": path, "reasons": reasons})
            if ctx.cancelled:
                return []
        for suspect in suspects[:MAX_SIG_CHECKS]:
            status = _signature_status(suspect["path"])
            if status != "Valid":
                suspect["reasons"].append(
                    f"nema validnog potpisa (status: {status})")
        if suspects:
            shown = suspects[:20]
            findings.append(Finding(
                id="suspicious-process", scanner=self.name,
                title=f"{len(suspects)} sumnjivih procesa (ne tvrdimo da je virus)",
                why="Proces bez validnog potpisa na neobicnoj lokaciji ili "
                    "autostart iz Temp-a su klasicni znaci zloupotrebe. "
                    "Ovo je sumnja na osnovu razloga ispod, ne dijagnoza.",
                severity="MEDIUM", impact="moguca zloupotreba sistema",
                risk="nizak: samo prijavljujemo, nista ne gasimo automatski",
                reversible=False,
                evidence={"count": len(suspects), "suspects": shown,
                          "truncated": len(suspects) > len(shown)},
                tech_details="Get-Process + Get-AuthenticodeSignature",
            ))

        try:
            rt_enabled = _ps_json("(Get-MpComputerStatus)."
                                  "RealTimeProtectionEnabled",
                                  timeout_s=30)
        except Exception:
            rt_enabled = None
        if rt_enabled is False:
            findings.append(Finding(
                id="suspicious-defender-off", scanner=self.name,
                title="Defender real-time zaštita je isključena",
                why="Bez real-time zastite sistem je otvoren za poznate "
                    "prijetnje. MujoFix ovo nikad sam ne mijenja — samo "
                    "javlja da provjeris.",
                severity="MEDIUM", impact="bez aktivne antivirus zastite",
                risk="nema: samo citamo status",
                reversible=False,
                evidence={"RealTimeProtectionEnabled": False},
                tech_details="Get-MpComputerStatus (read-only)",
            ))
        return findings

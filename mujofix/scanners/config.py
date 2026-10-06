"""Konfiguracija scanner: pokvaren PATH, TEMP/TMP, power plan, SFC tragovi."""

from __future__ import annotations

import os
import stat
import subprocess

from mujofix.core.models import Finding
from mujofix.platform import windows
from mujofix.scanners.base import ScanContext, Scanner, register

CBS_LOG = r"C:\Windows\Logs\CBS\CBS.log"
CBS_TAIL_BYTES = 512 * 1024


def _path_entries() -> list[str]:
    return [entry for entry in os.environ.get("PATH", "").split(os.pathsep)
            if entry]


def _world_writable(path: str) -> bool:
    try:
        return bool(os.stat(path).st_mode & stat.S_IWOTH)
    except OSError:
        return False


def _power_saver_active() -> tuple[bool, str]:
    proc = subprocess.run(["powercfg", "/getactivescheme"],
                          capture_output=True, text=True, timeout=30)
    out = proc.stdout.strip()
    saver_guid = "a1848308-3541-4fab-bc86-bb24e7d0f1f5"
    return saver_guid in out.lower() or "power saver" in out.lower(), out


def _cbs_failures() -> tuple[int, list[str]]:
    try:
        size = os.path.getsize(CBS_LOG)
        with open(CBS_LOG, "rb") as handle:
            handle.seek(max(0, size - CBS_TAIL_BYTES))
            tail = handle.read().decode("utf-8", errors="replace")
    except OSError:
        return 0, []
    bad = [line.strip() for line in tail.splitlines() if "Failed" in line]
    return len(bad), bad[-5:]


@register
class ConfigScanner(Scanner):
    name = "config"

    def _scan(self, ctx: ScanContext) -> list[Finding]:
        findings: list[Finding] = []
        entries = _path_entries()
        missing = [e for e in entries if not os.path.isdir(e)]
        writable = [e for e in entries
                    if os.path.isdir(e) and _world_writable(e)]
        if writable:
            findings.append(Finding(
                id="config-path-writable", scanner=self.name,
                title=f"{len(writable)} foldera u PATH-u moze mijenjati svako",
                why="Svijet-zapisiv folder u PATH-u znaci da bilo koji program "
                    "moze podmetnuti lazni .exe koji ces slucajno pokrenuti.",
                severity="MEDIUM", impact="rizik podmetanja programa",
                risk="srednji: skidanje prava pisanja trazi oprez",
                reversible=True,
                evidence={"entries": writable[:20]},
                tech_details="stat S_IWOTH nad PATH stavkama"))
        if missing:
            findings.append(Finding(
                id="config-path-missing", scanner=self.name,
                title=f"{len(missing)} PATH stavki ne postoji",
                why="Mrtve stavke u PATH-u usporavaju trazenje programa i "
                    "lome skripte koje racunaju na njih.",
                severity="LOW", impact="sporije pokretanje komandi",
                risk="nizak: ciscenje je reverzibilno", reversible=True,
                evidence={"entries": missing[:20]},
                tech_details="os.path.isdir nad PATH stavkama"))

        for var in ("TEMP", "TMP"):
            value = os.environ.get(var, "")
            if not value or not os.path.isdir(value):
                findings.append(Finding(
                    id="config-temp-var", scanner=self.name,
                    title=f"Varijabla {var} ne pokazuje na ispravan folder",
                    why="Programi pisu privremene fajlove u TEMP; losa putanja "
                        "rusi instalere i snimanja.",
                    severity="MEDIUM", impact="rusenje instalera/programa",
                    risk="nizak: postavljanje putanje je reverzibilno",
                    reversible=True,
                    evidence={"var": var, "value": value},
                    tech_details="os.environ + isdir"))

        if windows.is_windows() and not ctx.cancelled:
            try:
                saver, scheme = _power_saver_active()
            except OSError:
                saver, scheme = False, "nepoznato"
            if saver:
                findings.append(Finding(
                    id="config-power-saver", scanner=self.name,
                    title="Aktivan je štedljivi plan napajanja",
                    why="Power Saver smanjuje performanse da ustedi struju — "
                        "na desktopu je to cesto cista steta.",
                    severity="LOW", impact="smanjene performanse",
                    risk="nizak: promjena plana je reverzibilna",
                    reversible=True,
                    evidence={"scheme": scheme[:200]},
                    tech_details="powercfg /getactivescheme"))
            failures, sample = _cbs_failures()
            if failures > 5:
                findings.append(Finding(
                    id="config-sfc", scanner=self.name,
                    title=f"SFC tragovi: {failures} grešaka u CBS logu",
                    why="Servisiranje komponenti prijavljuje neuspjehe — "
                        "moguca ostecena sistemska datoteka (provjera: "
                        "sfc /scannow).",
                    severity="MEDIUM",
                    impact="moguca nestabilnost sistema",
                    risk="nizak: samo citamo log, ne mijenjamo nista",
                    reversible=False,
                    evidence={"failures": failures, "sample": sample},
                    tech_details=f"rep CBS.log ({CBS_TAIL_BYTES} B)"))
        return findings

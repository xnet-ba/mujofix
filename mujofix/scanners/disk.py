"""Disk scanner: slobodan prostor + temp (radi svugdje), WU cache i
Windows.old samo na Windowsu. SMART status dolazi u Fazi 5."""

from __future__ import annotations

import os
import shutil
import sys
import tempfile

from mujofix.core.models import Finding
from mujofix.platform import windows
from mujofix.scanners.base import ScanContext, Scanner, register

TEMP_BYTES_MEDIUM = 2 * 1024**3
WU_CACHE_DIR = r"C:\Windows\SoftwareDistribution\Download"
WINDOWS_OLD = r"C:\Windows.old"


def _dir_size(path: str, ctx: ScanContext, cap_files: int = 200_000) -> tuple[int, int]:
    """(bajtovi, broj fajlova); staje na cancel ili cap. Tih za nedostupno."""
    total = 0
    count = 0
    for _root, _dirs, files in os.walk(path):
        if ctx.cancelled or count >= cap_files:
            break
        for name in files:
            try:
                total += os.path.getsize(os.path.join(_root, name))
                count += 1
            except OSError:
                pass
    return total, count


def _gb(num_bytes: int) -> float:
    return round(num_bytes / 1024**3, 1)


@register
class DiskScanner(Scanner):
    name = "disk"

    def _scan(self, ctx: ScanContext) -> list[Finding]:
        findings: list[Finding] = []
        root = os.path.splitdrive(sys.executable)[0] + os.sep \
            if windows.is_windows() else os.sep
        try:
            usage = shutil.disk_usage(root)
        except OSError:
            return findings
        free_pct = 100.0 * usage.free / usage.total if usage.total else 100.0
        evidence = {"path": root, "total_gb": _gb(usage.total),
                    "free_gb": _gb(usage.free), "free_pct": round(free_pct, 1)}
        if free_pct < 10:
            findings.append(Finding(
                id="disk-almost-full", scanner=self.name,
                title=f"Disk je gotovo pun (ostalo {_gb(usage.free)} GB)",
                why="Kad ponestane slobodnog prostora, Windows usporava, "
                    "updatei pucaju, a programi se ruse pri snimanju.",
                severity="CRITICAL",
                impact="rizik rusenja programa i neuspjelih updatea",
                risk="nizak: brisemo samo temp i kes koji se sam obnavlja",
                reversible=False, evidence=evidence,
                tech_details=f"disk_usage({root})"))
        elif free_pct < 20:
            findings.append(Finding(
                id="disk-low", scanner=self.name,
                title=f"Malo slobodnog prostora ({_gb(usage.free)} GB)",
                why="Ispod 20% slobodno, vrijeme je za ciscenje prije nego "
                    "postane kriticno.",
                severity="MEDIUM", impact="usporenje i rizik punog diska",
                risk="nizak: brisemo samo temp i kes koji se sam obnavlja",
                reversible=False, evidence=evidence,
                tech_details=f"disk_usage({root})"))

        temp_dir = tempfile.gettempdir()
        temp_bytes, temp_files = _dir_size(temp_dir, ctx)
        if temp_bytes >= TEMP_BYTES_MEDIUM and not ctx.cancelled:
            findings.append(Finding(
                id="disk-temp", scanner=self.name,
                title=f"Privremeni fajlovi zauzimaju {_gb(temp_bytes)} GB",
                why="Temp se sam ne cisti; stari instalacioni ostaci i kes "
                    "mogu narasti do vise gigabajta.",
                severity="MEDIUM",
                impact=f"oslobadja se ~{_gb(temp_bytes)} GB",
                risk="nizak: brisu se fajlovi stariji od 7 dana, karantin 30 dana",
                reversible=True,
                evidence={"temp_dir": temp_dir, "bytes": temp_bytes,
                          "gb": _gb(temp_bytes), "files": temp_files},
                tech_details=f"walk({temp_dir})"))

        if windows.is_windows() and not ctx.cancelled:
            wu_bytes, wu_files = _dir_size(WU_CACHE_DIR, ctx)
            if wu_bytes >= TEMP_BYTES_MEDIUM:
                findings.append(Finding(
                    id="disk-wu-cache", scanner=self.name,
                    title=f"Windows Update kes zauzima {_gb(wu_bytes)} GB",
                    why="Preuzeti update paketi ostaju na disku i nakon instalacije.",
                    severity="LOW", impact=f"oslobadja se ~{_gb(wu_bytes)} GB",
                    risk="nizak: kes se ponovo preuzme ako zatreba",
                    reversible=True,
                    evidence={"path": WU_CACHE_DIR, "bytes": wu_bytes,
                              "files": wu_files},
                    tech_details=f"walk({WU_CACHE_DIR})"))
            if os.path.isdir(WINDOWS_OLD):
                old_bytes, _n = _dir_size(WINDOWS_OLD, ctx)
                findings.append(Finding(
                    id="disk-windows-old", scanner=self.name,
                    title=f"Stara instalacija Windowsa ({_gb(old_bytes)} GB)",
                    why="Folder Windows.old ostaje nakon nadogradnje; brise se "
                        "sam nakon ~10 dana, ali do tada jede disk.",
                    severity="LOW", impact=f"oslobadja se ~{_gb(old_bytes)} GB",
                    risk="srednji: nakon brisanja nema povratka na staru verziju",
                    reversible=False,
                    evidence={"path": WINDOWS_OLD, "bytes": old_bytes},
                    tech_details=f"walk({WINDOWS_OLD})"))
        return findings

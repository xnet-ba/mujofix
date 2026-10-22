"""Disk scanner: slobodan prostor + temp (radi svugdje), WU cache i
Windows.old samo na Windowsu. SMART status dolazi u Fazi 5."""

from __future__ import annotations

import os
import shutil
import sys
import tempfile

from mujofix.core.models import Finding
from mujofix.platform import windows
from mujofix.scanners.base import ScanContext, Scanner, register, t

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
                title=t(ctx, "sc_disk_almost_full_title", gb=_gb(usage.free)),
                why=t(ctx, "sc_disk_almost_full_why"),
                severity="CRITICAL",
                impact=t(ctx, "sc_disk_almost_full_impact"),
                risk=t(ctx, "sc_disk_temp_cache_risk"),
                reversible=False, evidence=evidence,
                tech_details=f"disk_usage({root})"))
        elif free_pct < 20:
            findings.append(Finding(
                id="disk-low", scanner=self.name,
                title=t(ctx, "sc_disk_low_title", gb=_gb(usage.free)),
                why=t(ctx, "sc_disk_low_why"),
                severity="MEDIUM", impact=t(ctx, "sc_disk_low_impact"),
                risk=t(ctx, "sc_disk_temp_cache_risk"),
                reversible=False, evidence=evidence,
                tech_details=f"disk_usage({root})"))

        temp_dir = tempfile.gettempdir()
        temp_bytes, temp_files = _dir_size(temp_dir, ctx)
        if temp_bytes >= TEMP_BYTES_MEDIUM and not ctx.cancelled:
            findings.append(Finding(
                id="disk-temp", scanner=self.name,
                title=t(ctx, "sc_disk_temp_title", gb=_gb(temp_bytes)),
                why=t(ctx, "sc_disk_temp_why"),
                severity="MEDIUM",
                impact=t(ctx, "sc_disk_temp_impact", gb=_gb(temp_bytes)),
                risk=t(ctx, "sc_disk_temp_risk"),
                reversible=True,
                evidence={"temp_dir": temp_dir, "bytes": temp_bytes,
                          "gb": _gb(temp_bytes), "files": temp_files},
                tech_details=f"walk({temp_dir})"))

        if windows.is_windows() and not ctx.cancelled:
            wu_bytes, wu_files = _dir_size(WU_CACHE_DIR, ctx)
            if wu_bytes >= TEMP_BYTES_MEDIUM:
                findings.append(Finding(
                    id="disk-wu-cache", scanner=self.name,
                    title=t(ctx, "sc_disk_wu_title", gb=_gb(wu_bytes)),
                    why=t(ctx, "sc_disk_wu_why"),
                    severity="LOW",
                    impact=t(ctx, "sc_disk_wu_impact", gb=_gb(wu_bytes)),
                    risk=t(ctx, "sc_disk_wu_risk"),
                    reversible=True,
                    evidence={"path": WU_CACHE_DIR, "bytes": wu_bytes,
                              "files": wu_files},
                    tech_details=f"walk({WU_CACHE_DIR})"))
            if os.path.isdir(WINDOWS_OLD):
                old_bytes, _n = _dir_size(WINDOWS_OLD, ctx)
                findings.append(Finding(
                    id="disk-windows-old", scanner=self.name,
                    title=t(ctx, "sc_disk_old_title", gb=_gb(old_bytes)),
                    why=t(ctx, "sc_disk_old_why"),
                    severity="LOW",
                    impact=t(ctx, "sc_disk_old_impact", gb=_gb(old_bytes)),
                    risk=t(ctx, "sc_disk_old_risk"),
                    reversible=False,
                    evidence={"path": WINDOWS_OLD, "bytes": old_bytes},
                    tech_details=f"walk({WINDOWS_OLD})"))
        return findings

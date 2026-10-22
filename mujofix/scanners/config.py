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
        # POSIX stat bitovi na Windowsu varaju (ACL != mode); tamo ranjive
        # dozvole provjerava permissions scanner kroz icacls.
        writable = [] if windows.is_windows() else [
            e for e in entries if os.path.isdir(e) and _world_writable(e)]
        if writable:
            findings.append(Finding(
                id="config-path-writable", scanner=self.name,
                title=self.t("sc_config_path_writable_title", n=len(writable)),
                why=self.t("sc_config_path_writable_why"),
                severity="MEDIUM",
                impact=self.t("sc_config_path_writable_impact"),
                risk=self.t("sc_config_path_writable_risk"),
                reversible=True,
                evidence={"entries": writable[:20]},
                tech_details=self.t("sc_config_path_writable_tech")))
        if missing:
            findings.append(Finding(
                id="config-path-missing", scanner=self.name,
                title=self.t("sc_config_path_missing_title", n=len(missing)),
                why=self.t("sc_config_path_missing_why"),
                severity="LOW", impact=self.t("sc_config_path_missing_impact"),
                risk=self.t("sc_config_path_missing_risk"), reversible=True,
                evidence={"entries": missing[:20]},
                tech_details=self.t("sc_config_path_missing_tech")))

        for var in ("TEMP", "TMP"):
            value = os.environ.get(var, "")
            if not value or not os.path.isdir(value):
                findings.append(Finding(
                    id="config-temp-var", scanner=self.name,
                    title=self.t("sc_config_temp_title", var=var),
                    why=self.t("sc_config_temp_why"),
                    severity="MEDIUM", impact=self.t("sc_config_temp_impact"),
                    risk=self.t("sc_config_temp_risk"),
                    reversible=True,
                    evidence={"var": var, "value": value},
                    tech_details=self.t("sc_config_temp_tech")))

        if windows.is_windows() and not ctx.cancelled:
            try:
                saver, scheme = _power_saver_active()
            except OSError:
                saver, scheme = False, self.t("sc_common_unknown")
            if saver:
                findings.append(Finding(
                    id="config-power-saver", scanner=self.name,
                    title=self.t("sc_config_power_title"),
                    why=self.t("sc_config_power_why"),
                    severity="LOW", impact=self.t("sc_config_power_impact"),
                    risk=self.t("sc_config_power_risk"),
                    reversible=True,
                    evidence={"scheme": scheme[:200]},
                    tech_details=self.t("sc_config_power_tech")))
            failures, sample = _cbs_failures()
            if failures > 5:
                findings.append(Finding(
                    id="config-sfc", scanner=self.name,
                    title=self.t("sc_config_sfc_title", n=failures),
                    why=self.t("sc_config_sfc_why"),
                    severity="MEDIUM",
                    impact=self.t("sc_config_sfc_impact"),
                    risk=self.t("sc_config_sfc_risk"),
                    reversible=False,
                    evidence={"failures": failures, "sample": sample},
                    tech_details=self.t("sc_config_sfc_tech",
                                         n=CBS_TAIL_BYTES)))
        return findings

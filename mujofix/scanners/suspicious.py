"""Sumnjivi procesi (samo Windows): autostart iz Temp/AppData + potpis.

Nikad ne tvrdi "virus" — samo "sumnjivo, razlozi: ...". Defender status se
cita (read-only), nikad se ne mijenja. Potpis: Get-AuthenticodeSignature.
"""

from __future__ import annotations

import os

from mujofix.core.models import Finding
from mujofix.platform import windows
from mujofix.scanners.base import ScanContext, Scanner, register
from mujofix.scanners.startup import RUN_KEYS

_PS_PROCESS_CMD = "Get-Process | Select-Object Name,Id,Path | ConvertTo-Json"
MAX_SIG_CHECKS = 20


from mujofix.platform.powershell import ps_json as _ps_json


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


# Siroki izuzeci koji ozbiljno slabe zastitu (cesto trik da malware prodje).
BROAD_SUFFIX_ROOTS = ("c:\\", "d:\\", "*")
BROAD_PARTS = ("\\users\\", "\\appdata\\", "\\temp\\", "\\downloads\\")


def _exclusions() -> dict:
    """Izuzeci iz Get-MpPreference (path/process/extension)."""
    command = (
        "$p = Get-MpPreference; [pscustomobject]@{ "
        "Path = @($p.ExclusionPath); Process = @($p.ExclusionProcess); "
        "Extension = @($p.ExclusionExtension) } | ConvertTo-Json -Depth 3"
    )
    data = _ps_json(command, timeout_s=30)
    if not isinstance(data, dict):
        return {}
    out = {}
    for key in ("Path", "Process", "Extension"):
        value = data.get(key)
        if isinstance(value, str):
            value = [value]
        out[key.lower()] = [str(v) for v in (value or []) if str(v).strip()]
    return out


def _is_broad(entry: str) -> bool:
    """Da li izuzetak pokriva previse (cijeli disk, profil, Temp, Downloads)."""
    lowered = os.path.expandvars(entry).lower()
    if lowered.strip() in BROAD_SUFFIX_ROOTS:
        return True
    return any(part in lowered for part in BROAD_PARTS)


@register
class SuspiciousScanner(Scanner):
    name = "suspicious"

    def is_available(self) -> bool:
        return windows.is_windows()

    def unavailable_reason(self) -> str:
        return self.t("sc_susp_unavailable")

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
                title=self.t("sc_susp_title", n=len(suspects)),
                why=self.t("sc_susp_why"),
                severity="MEDIUM", impact=self.t("sc_susp_impact"),
                risk=self.t("sc_susp_risk"),
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
                title=self.t("sc_susp_defender_title"),
                why=self.t("sc_susp_defender_why"),
                severity="MEDIUM", impact=self.t("sc_susp_defender_impact"),
                risk=self.t("sc_susp_defender_risk"),
                reversible=False,
                evidence={"RealTimeProtectionEnabled": False},
                tech_details="Get-MpComputerStatus (read-only)",
            ))

        try:
            ex = _exclusions()
        except Exception:
            ex = {}
        total = sum(len(v) for v in ex.values())
        if total:
            flagged = [entry for values in ex.values() for entry in values
                       if _is_broad(entry)]
            severity = "MEDIUM" if flagged else "LOW"
            findings.append(Finding(
                id="defender-exclusions", scanner=self.name,
                title=self.t("sc_defender_excl_title", n=total),
                why=self.t("sc_defender_excl_why"),
                severity=severity,
                impact=self.t("sc_defender_excl_impact"),
                risk=self.t("sc_defender_excl_risk"),
                reversible=True,  # izuzeci se mogu ukloniti (ali MI to ne radimo)
                evidence={"count": total, "broad": flagged[:5],
                          "path": ex.get("path", [])[:10],
                          "process": ex.get("process", [])[:10],
                          "extension": ex.get("extension", [])[:10]},
                tech_details="Get-MpPreference (read-only)",
            ))
        return findings

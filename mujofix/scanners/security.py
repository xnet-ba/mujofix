"""Security scanner: osnovna sigurnosna postavka (SAMO CITANJE).

Provjere (svaka nezavisna — ako jedna ne moze da se izvrsi, preskace se bez
tvrdnje, a ostale se i dalje rade):
- BitLocker na sistemskom disku (sifrovanje podataka)
- Secure Boot (UEFI lanac pouzdanja)
- TPM (cesto uslov za BitLocker/Windows Hello)
- Windows Update servis (da li je iskljucen)

Iskrenost: ako se NIJEDNA provjera ne moze izvrsiti, scanner se prijavljuje kao
`skipped` (nikad tiho "sve je u redu"). App nista ne mijenja — mijenjanje
zastitnih politika je izvan politike aplikacije, pa ovi nalazi NEMAJU akcije.
"""

from __future__ import annotations

from mujofix.core.models import Finding
from mujofix.platform import windows
from mujofix.platform.powershell import ps_json
from mujofix.scanners.base import ScanContext, Scanner, register

_PS_BITLOCKER = (
    "$v = Get-BitLockerVolume -MountPoint ($env:SystemDrive + '\\') "
    "-ErrorAction Stop; "
    "[pscustomobject]@{ Status = \"$($v.ProtectionStatus)\"; "
    "Volume = \"$($v.VolumeStatus)\" } | ConvertTo-Json"
)
_PS_SECUREBOOT = (
    "try { if (Confirm-SecureBootUEFI) { 'True' } else { 'False' } } "
    "catch { 'Unsupported' }"
)
_PS_TPM = (
    "$t = Get-Tpm -ErrorAction Stop; "
    "[pscustomobject]@{ Present = $t.TpmPresent; Ready = $t.TpmReady } | "
    "ConvertTo-Json"
)
_PS_WUAUSERV = (
    "[pscustomobject]@{ StartType = \"$((Get-Service wuauserv).StartType)\" } "
    "| ConvertTo-Json"
)


def _ps(command: str) -> object:
    """PowerShell poziv (odvojeno zbog testova)."""
    return ps_json(command, timeout_s=60)


@register
class SecurityScanner(Scanner):
    name = "security"

    def is_available(self) -> bool:
        return windows.is_windows()

    def unavailable_reason(self) -> str:
        return self.t("sc_sec_unavailable")

    # -- provjere (vracaju Finding ili None; dize ako provjera nije izvediva) --
    def _bitlocker(self) -> Finding | None:
        data = _ps(_PS_BITLOCKER)
        status = str((data or {}).get("Status", "")).lower() \
            if isinstance(data, dict) else ""
        if not status:
            raise RuntimeError("nema ProtectionStatus")
        if status == "on":
            return None
        return Finding(
            id="bitlocker-off", scanner=self.name,
            title=self.t("sc_sec_bitlocker_title", status=status),
            why=self.t("sc_sec_bitlocker_why"),
            severity="MEDIUM", impact=self.t("sc_sec_bitlocker_impact"),
            risk=self.t("sc_sec_readonly_risk"), reversible=True,
            evidence={"status": status,
                      "volume": (data or {}).get("Volume", "")},
            tech_details="Get-BitLockerVolume (read-only)",
        )

    def _secureboot(self) -> Finding | None:
        data = _ps(_PS_SECUREBOOT)
        value = str(data or "").strip()
        if value not in ("True", "False", "Unsupported"):
            raise RuntimeError(f"neocekivan odgovor: {value[:40]}")
        if value != "False":
            return None
        return Finding(
            id="secureboot-off", scanner=self.name,
            title=self.t("sc_sec_sb_title"),
            why=self.t("sc_sec_sb_why"),
            severity="MEDIUM", impact=self.t("sc_sec_sb_impact"),
            risk=self.t("sc_sec_readonly_risk"), reversible=True,
            evidence={"SecureBoot": False},
            tech_details="Confirm-SecureBootUEFI (read-only)",
        )

    def _tpm(self) -> Finding | None:
        data = _ps(_PS_TPM)
        present = bool((data or {}).get("Present")) \
            if isinstance(data, dict) else False
        ready = bool((data or {}).get("Ready")) if isinstance(data, dict) else False
        if present and ready:
            return None
        return Finding(
            id="tpm-absent", scanner=self.name,
            title=self.t("sc_sec_tpm_title"),
            why=self.t("sc_sec_tpm_why"),
            severity="LOW", impact=self.t("sc_sec_tpm_impact"),
            risk=self.t("sc_sec_readonly_risk"), reversible=True,
            evidence={"present": present, "ready": ready},
            tech_details="Get-Tpm (read-only)",
        )

    def _wuauserv(self) -> Finding | None:
        data = _ps(_PS_WUAUSERV)
        start_type = str((data or {}).get("StartType", "")).lower() \
            if isinstance(data, dict) else ""
        if not start_type:
            raise RuntimeError("nema StartType")
        if start_type not in ("disabled", "manual"):
            return None
        return Finding(
            id="wuauserv-disabled", scanner=self.name,
            title=self.t("sc_sec_wu_title", state=start_type),
            why=self.t("sc_sec_wu_why"),
            severity="MEDIUM" if start_type == "disabled" else "LOW",
            impact=self.t("sc_sec_wu_impact"),
            risk=self.t("sc_sec_readonly_risk"), reversible=True,
            evidence={"StartType": start_type},
            tech_details="Get-Service wuauserv (read-only)",
        )

    def _scan(self, ctx: ScanContext) -> list[Finding]:
        findings: list[Finding] = []
        checks = 0
        for check in (self._bitlocker, self._secureboot, self._tpm,
                      self._wuauserv):
            if ctx.cancelled:
                return findings
            try:
                finding = check()
            except Exception:
                continue  # ovu provjeru ne mozemo izvesti — bez tvrdnje
            checks += 1
            if finding is not None:
                findings.append(finding)
        if checks == 0:
            # nista nije provjereno -> prijavi kao skipped, ne "sve je u redu"
            raise RuntimeError(self.t("sc_sec_nothing_checked"))
        return findings

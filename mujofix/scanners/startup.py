"""Startup scanner: Run/RunOnce kljucevi + Startup folderi.

Heuristika broja stavki je grub orijentir, ne mjerenje boot vremena —
tekst nalaza to izricito kaze (anti-halucinacija). Stvarno vrijeme boot-a
(Event Log / Diagnostics-Performance) dolazi u Fazi 5.
"""

from __future__ import annotations

from mujofix.core.models import Finding
from mujofix.platform import windows
from mujofix.scanners.base import ScanContext, Scanner, register

RUN_KEYS = (
    ("HKCU", r"Software\Microsoft\Windows\CurrentVersion\Run"),
    ("HKCU", r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
    ("HKLM", r"Software\Microsoft\Windows\CurrentVersion\Run"),
    ("HKLM", r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
)

MEDIUM_THRESHOLD = 10


@register
class StartupScanner(Scanner):
    name = "startup"

    def is_available(self) -> bool:
        return windows.is_windows()

    def unavailable_reason(self) -> str:
        return self.t("sc_startup_unavailable")

    def _scan(self, ctx: ScanContext) -> list[Finding]:
        items: list[dict[str, str]] = []
        for hive, path in RUN_KEYS:
            for entry_name, command in windows.read_reg_values(hive, path).items():
                items.append(
                    {"source": f"{hive}\\{path}", "name": entry_name,
                     "command": command}
                )
            if ctx.cancelled:
                return []
        for folder in windows.startup_folders():
            for entry_name in windows.list_folder_entries(folder):
                items.append(
                    {"source": folder, "name": entry_name, "command": entry_name}
                )
            if ctx.cancelled:
                return []
        count = len(items)
        if count == 0:
            return []
        severity = "MEDIUM" if count >= MEDIUM_THRESHOLD else "LOW"
        impact_key = ("sc_startup_impact_many" if count >= MEDIUM_THRESHOLD
                      else "sc_startup_impact_few")
        return [Finding(
            id="startup-count",
            scanner=self.name,
            title=self.t("sc_startup_title", n=count),
            why=self.t("sc_startup_why"),
            severity=severity,
            impact=self.t(impact_key, n=count),
            risk=self.t("sc_startup_risk"),
            reversible=True,
            evidence={"count": count, "items": items,
                      "threshold_medium": MEDIUM_THRESHOLD},
            tech_details=self.t("sc_startup_tech"),
        )]

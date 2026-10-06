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
        return "startup skeniranje radi samo na Windowsu"

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
        return [Finding(
            id="startup-count",
            scanner=self.name,
            title=f"{count} programa se pali s Windowsom",
            why=("Programi koji se pale s sistemom produzuju prijavu i trose "
                 "memoriju u pozadini. Broj stavki je orijentir — nije izmjereno "
                 "stvarno vrijeme boot-a."),
            severity=severity,
            impact=(f"sporija prijava i {count} pozadinskih programa" if count >= 10
                    else "blago usporenje prijave"),
            risk="nizak: onemogucavanje stavke se ponistava jednim klikom",
            reversible=True,
            evidence={"count": count, "items": items,
                      "threshold_medium": MEDIUM_THRESHOLD},
            tech_details="Run/RunOnce kljucevi + Startup folderi; "\
                         "Scheduled Tasks i servisi dolaze u Fazi 5.",
        )]

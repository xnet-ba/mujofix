"""Servisi scanner (samo Windows): automatski servisi koji ne rade.

Jedan poziv PowerShell Get-Service -> JSON (bez pywin32 zavisnosti).
Event ID 7031/7034 iz Event Loga dolazi u Fazi 5; tekst to izricito kaze.
"""

from __future__ import annotations

import json
import subprocess

from mujofix.core.models import Finding
from mujofix.platform import windows
from mujofix.scanners.base import ScanContext, Scanner, register

_PS = ("powershell", "-NoProfile", "-NonInteractive", "-Command",
        "Get-Service | Select-Object Name,Status,StartType | ConvertTo-Json")


def _query_services() -> list[dict]:
    proc = subprocess.run(list(_PS), capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        raise RuntimeError(f"Get-Service pao: {proc.stderr.strip()[-200:]}")
    data = json.loads(proc.stdout or "[]")
    return data if isinstance(data, list) else [data]


@register
class ServicesScanner(Scanner):
    name = "services"

    def is_available(self) -> bool:
        return windows.is_windows()

    def unavailable_reason(self) -> str:
        return "servisi postoje samo na Windowsu"

    def _scan(self, ctx: ScanContext) -> list[Finding]:
        services = _query_services()
        dead = sorted(
            svc.get("Name", "?") for svc in services
            if str(svc.get("StartType", "")).lower() == "automatic"
            and str(svc.get("Status", "")).lower() == "stopped"
        )
        if not dead:
            return []
        shown = dead[:20]
        return [Finding(
            id="services-auto-stopped", scanner=self.name,
            title=f"{len(dead)} automatskih servisa ne radi",
            why="Servis podesen na automatski start bi morao raditi nakon "
                "boot-a. Zaustavljen automatski servis znaci rusenje ili "
                "pogresnu konfiguraciju. Istorija rusenja (Event ID 7031/7034) "
                "se ne cita u ovoj fazi.",
            severity="MEDIUM",
            impact="funkcije tih servisa ne rade (mreza, stampanje, update...)",
            risk="srednji: restart servisa je reverzibilan, ali uzrok rusenja "
                 "moze ostati",
            reversible=True,
            evidence={"count": len(dead), "sample": shown,
                      "truncated": len(dead) > len(shown)},
            tech_details="Get-Service (Name,Status,StartType)",
        )]

"""Drajveri scanner (samo Windows): zastarjeli third-party drajveri (pnputil).

Defanzivno parsiranje: neprepoznat ispis ili pad alata = skipped izvjestaj
(baza hvata izuzetak), nikad laznih podataka.
"Programi koji se dugo ne koriste" se ne mjeri — Windows ne prati koristenje
po programu pa bi svaka tvrdnja bila halucinacija (vidi tech_details).
"""

from __future__ import annotations

import re
import subprocess
from datetime import date, datetime

from mujofix.core.models import Finding
from mujofix.platform import windows
from mujofix.scanners.base import ScanContext, Scanner, register

OLD_YEARS = 8
DATE_FORMATS = ("%m/%d/%Y", "%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y")


def _run_pnputil() -> str:
    proc = subprocess.run(["pnputil", "/enum-drivers"],
                          capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        raise RuntimeError(f"pnputil pao: {proc.stderr.strip()[-200:]}")
    return proc.stdout


def _parse_drivers(text: str) -> list[dict]:
    drivers: list[dict] = []
    current: dict = {}
    for line in text.splitlines() + [""]:
        if not line.strip():
            if current.get("oem"):
                drivers.append(current)
            current = {}
            continue
        key, _, value = line.partition(":")
        key, value = key.strip().lower(), value.strip()
        if key == "published name" and re.fullmatch(r"oem\d+\.inf", value):
            current["oem"] = value
        elif key == "driver package provider":
            current["provider"] = value
        elif key == "class":
            current["class"] = value
        elif key == "driver date and version":
            parts = value.split()
            current["date_raw"] = parts[0] if parts else ""
            current["version"] = " ".join(parts[1:])
    return drivers


def _parse_date(raw: str) -> date | None:
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            pass
    return None


@register
class DriversScanner(Scanner):
    name = "drivers"

    def is_available(self) -> bool:
        return windows.is_windows()

    def unavailable_reason(self) -> str:
        return "pnputil postoji samo na Windowsu"

    def _scan(self, ctx: ScanContext) -> list[Finding]:
        try:
            drivers = _parse_drivers(_run_pnputil())
        except (OSError, RuntimeError) as exc:
            raise RuntimeError(f"pnputil nedostupan: {exc}")
        if not drivers:
            raise RuntimeError("pnputil ispis neprepoznat (nema oem*.inf)")
        old = []
        for driver in drivers:
            day = _parse_date(driver.get("date_raw", ""))
            if day is not None and (date.today() - day).days >= OLD_YEARS * 365:
                old.append({**driver, "date": day.isoformat()})
            if ctx.cancelled:
                return []
        if not old:
            return []
        return [Finding(
            id="drivers-old", scanner=self.name,
            title=f"{len(old)} drajvera starijih od {OLD_YEARS} godina",
            why="Zastarjeli drajveri znaju rusiti sistem nakon updatea "
                "Windowsa; noviji donose ispravke stabilnosti.",
            severity="MEDIUM", impact="moguca nestabilnost/plavi ekran",
            risk="srednji: update drajvera trazi restart; rollback kroz "
                 "Device Manager",
            reversible=True,
            evidence={"count": len(old), "drivers": old[:20],
                      "total_third_party": len(drivers)},
            tech_details=("pnputil /enum-drivers. Nekoristene programe ne "
                          "prijavljujemo: Windows ne mjeri koristenje po "
                          "programu."),
        )]

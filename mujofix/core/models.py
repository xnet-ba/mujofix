"""Model nalaza (Faza 1): svaki nalaz nosi dokaz, inace se ne prikazuje."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

Severity = Literal["CRITICAL", "MEDIUM", "LOW"]


@dataclass(frozen=True)
class Finding:
    """Jedan problem obicnim jezikom + masinski dokaz."""

    id: str  # stabilan, npr. "startup-count"
    scanner: str  # ime scannera, npr. "startup"
    title: str  # obican jezik: "Puno programa se pali s Windowsom (14)"
    why: str  # zasto je ovo problem (1-2 recenice)
    severity: Severity
    impact: str  # procjena uticaja obicnim jezikom
    risk: str  # rizik popravke obicnim jezikom
    reversible: bool  # da li se popravka moze poništiti
    evidence: dict  # sirova mjerenja: kljucevi, putanje, brojke
    tech_details: str = ""  # prosirivi detalji za napredne korisnike

    def __post_init__(self) -> None:
        if not self.evidence:
            raise ValueError(f"nalaz {self.id} bez evidence se ne smije prikazati")
        if self.severity not in ("CRITICAL", "MEDIUM", "LOW"):
            raise ValueError(f"nepoznata ozbiljnost: {self.severity}")

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ScanReport:
    """Rezultat jednog scannera: nalazi ili razlog preskakanja."""

    scanner: str
    findings: list[Finding] = field(default_factory=list)
    duration_s: float = 0.0
    skipped: str | None = None  # None = izvrsen; tekst = zasto nije

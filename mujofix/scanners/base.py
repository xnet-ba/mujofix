"""Scanner plugin interfejs: svi moduli imaju isti ugovor."""

from __future__ import annotations

import abc
import threading
import time
from dataclasses import dataclass, field

from mujofix.core.models import Finding, ScanReport


@dataclass
class ScanContext:
    """Dijeljeni kontekst skeniranja (otkazivanje, buduce: putanje, jezik)."""

    cancel: threading.Event = field(default_factory=threading.Event)

    @property
    def cancelled(self) -> bool:
        return self.cancel.is_set()


class Scanner(abc.ABC):
    """Baza za sve scannere. scan() nikad ne baca — vrati ScanReport."""

    name: str = "nepoznat"

    def is_available(self) -> bool:
        """False -> graceful skip uz razlog (npr. samo-Windows modul)."""
        return True

    def unavailable_reason(self) -> str:
        return "modul nije podrzan na ovoj platformi"

    @abc.abstractmethod
    def _scan(self, ctx: ScanContext) -> list[Finding]:
        ...

    def scan(self, ctx: ScanContext) -> ScanReport:
        started = time.time()
        if not self.is_available():
            return ScanReport(scanner=self.name, skipped=self.unavailable_reason())
        try:
            findings = self._scan(ctx)
        except Exception as exc:  # scanner ne smije srusiti cijeli SCAN
            return ScanReport(
                scanner=self.name,
                skipped=f"greska scannera ({type(exc).__name__}): {exc}",
            )
        return ScanReport(
            scanner=self.name,
            findings=findings,
            duration_s=time.time() - started,
        )


REGISTRY: dict[str, type[Scanner]] = {}


def register(cls: type[Scanner]) -> type[Scanner]:
    """Dekorator: @register nad klasom scannera."""
    REGISTRY[cls.name] = cls
    return cls

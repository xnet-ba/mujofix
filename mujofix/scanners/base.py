"""Scanner plugin interfejs: svi moduli imaju isti ugovor."""

from __future__ import annotations

import abc
import threading
import time
from dataclasses import dataclass, field

from mujofix.core.models import Finding, ScanReport


@dataclass
class ScanContext:
    """Dijeljeni kontekst skeniranja (otkazivanje, jezik nalaza)."""

    cancel: threading.Event = field(default_factory=threading.Event)
    lang: str = "bs"  # jezik teksta nalaza (scanner ga pise preko `t(ctx, ...)`)

    @property
    def cancelled(self) -> bool:
        return self.cancel.is_set()


class Scanner(abc.ABC):
    """Baza za sve scannere. scan() nikad ne baca — vrati ScanReport."""

    name: str = "nepoznat"
    lang: str = "bs"  # postavlja scan() iz ctx.lang (i unavailable_reason ga vidi)

    def t(self, key: str, **fmt: object) -> str:
        """Prevedi tekst nalaza na jezik skeniranja (jedan put za sve scannere)."""
        from mujofix.i18n.strings import tr

        return tr(key, self.lang, **fmt)

    def is_available(self) -> bool:
        """False -> graceful skip uz razlog (npr. samo-Windows modul)."""
        return True

    def unavailable_reason(self) -> str:
        return self.t("sc_unavailable_generic")

    @abc.abstractmethod
    def _scan(self, ctx: ScanContext) -> list[Finding]:
        ...

    def scan(self, ctx: ScanContext) -> ScanReport:
        started = time.time()
        self.lang = ctx.lang  # jezik nalaza (i "skipped" razloga)
        if not self.is_available():
            return ScanReport(scanner=self.name, skipped=self.unavailable_reason())
        try:
            findings = self._scan(ctx)
        except Exception as exc:  # scanner ne smije srusiti cijeli SCAN
            return ScanReport(
                scanner=self.name,
                skipped=self.t("sc_error", kind=type(exc).__name__, e=exc),
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

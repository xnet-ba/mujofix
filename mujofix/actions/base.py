"""Action katalog + Runner (Faza 2): svaka akcija ima precondition, snapshot,
apply, verify i rollback. Bez rollback()-a nema auto-fixa, samo preporuka.

Redoslijed izvrsenja: precondition -> snapshot -> apply -> verify.
Pad bilo gdje nakon snapshot-a -> rollback -> izvijesti. Dry-run nista ne dira.
"""

from __future__ import annotations

import abc
import json
import os
import shutil
import time
from dataclasses import dataclass, field


@dataclass
class ActionContext:
    """Karantin dir (injektabilan za testove), dry-run, otkazivanje."""

    quarantine_dir: str
    dry_run: bool = False
    cancelled: bool = False


@dataclass
class ActionResult:
    action: str
    ok: bool
    verified: bool
    rolled_back: bool
    message: str
    duration_s: float = 0.0
    state: dict | None = None  # snapshot uspjesnog koraka (za "Ponisti sve")


class Action(abc.ABC):
    """Ugovor za svaku akciju kataloga."""

    name: str = "nepoznata"
    description: str = ""  # obican jezik: sta cemo uraditi
    risk: str = "nepoznat"  # nizak / srednji / visok + kako se ponistava
    needs_elevation: bool = False  # True -> ide kroz UAC executor

    @abc.abstractmethod
    def precondition(self, ctx: ActionContext) -> tuple[bool, str]:
        """(moze, razlog). False -> akcija se ne pokusava."""
        ...

    @abc.abstractmethod
    def snapshot(self, ctx: ActionContext) -> dict:
        """Sacuvaj stanje potrebno za rollback. Bez nuspojava na sistem."""
        ...

    @abc.abstractmethod
    def apply(self, ctx: ActionContext, state: dict) -> None:
        """Izvrsi promjenu."""
        ...

    @abc.abstractmethod
    def verify(self, ctx: ActionContext, state: dict) -> tuple[bool, str]:
        """Ponovo izmjeri isto sto je nalaz detektovao."""
        ...

    @abc.abstractmethod
    def rollback(self, ctx: ActionContext, state: dict) -> None:
        """Vrati stanje iz snapshot-a. Mora biti idempotentan."""
        ...


def quarantine_file(path: str, quarantine_dir: str) -> dict:
    """Premjesti fajl u karantin (ne trajno brisanje). Vrati zapis za manifest."""
    os.makedirs(quarantine_dir, exist_ok=True)
    base = os.path.basename(path)
    dest = os.path.join(quarantine_dir, f"{int(time.time())}_{base}")
    shutil.move(path, dest)
    return {"original": path, "quarantined": dest}


def restore_quarantined(record: dict) -> None:
    """Vrati fajl iz karantina na originalnu putanju (idempotentno)."""
    dest, original = record["quarantined"], record["original"]
    if os.path.exists(original) or not os.path.exists(dest):
        return
    os.makedirs(os.path.dirname(original), exist_ok=True)
    shutil.move(dest, original)


def save_manifest(quarantine_dir: str, name: str, records: list[dict]) -> str:
    path = os.path.join(quarantine_dir, f"{name}.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(records, handle, indent=2)
    return path


CATALOG: dict[str, type[Action]] = {}


def register(cls: type[Action]) -> type[Action]:
    CATALOG[cls.name] = cls
    return cls


class Runner:
    """Deterministicki executor: samo akcije iz kataloga, sve u audit log."""

    def __init__(self) -> None:
        self.audit: list[dict] = []

    def _log(self, action: str, phase: str, ok: bool, message: str) -> None:
        self.audit.append({"action": action, "phase": phase,
                           "ok": ok, "message": message})

    def run(self, action: Action, ctx: ActionContext) -> ActionResult:
        started = time.time()
        name = action.name
        if ctx.cancelled:
            self._log(name, "cancelled", False, "otkazano prije pocetka")
            return ActionResult(name, False, False, False, "otkazano", 0.0)
        if ctx.dry_run:
            ok, reason = action.precondition(ctx)
            self._log(name, "dry-run", ok, f"precondition: {reason}")
            return ActionResult(name, ok, False, False,
                                f"dry-run, nista nije mijenjano: {reason}", 0.0)
        ok, reason = action.precondition(ctx)
        if not ok:
            self._log(name, "precondition", False, reason)
            return ActionResult(name, False, False, False,
                                f"precondition pao: {reason}",
                                time.time() - started)
        try:
            state = action.snapshot(ctx)
        except Exception as exc:
            self._log(name, "snapshot", False, str(exc))
            return ActionResult(name, False, False, False,
                                f"snapshot pao: {exc}", time.time() - started)
        try:
            action.apply(ctx, state)
        except Exception as exc:
            self._rollback_quietly(action, ctx, state)
            self._log(name, "apply", False, str(exc))
            return ActionResult(name, False, False, True,
                                f"apply pao, vraceno: {exc}",
                                time.time() - started)
        verified, details = action.verify(ctx, state)
        if not verified:
            self._rollback_quietly(action, ctx, state)
            self._log(name, "verify", False, details)
            return ActionResult(name, False, False, True,
                                f"verifikacija pala, vraceno: {details}",
                                time.time() - started)
        self._log(name, "done", True, details)
        return ActionResult(name, True, True, False, details,
                            time.time() - started, state=state)

    def _rollback_quietly(self, action: Action, ctx: ActionContext,
                         state: dict) -> None:
        try:
            action.rollback(ctx, state)
            self._log(action.name, "rollback", True, "stanje vraceno")
        except Exception as exc:
            self._log(action.name, "rollback", False, f"ROLLBACK PAO: {exc}")

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
    """Karantin dir (injektabilan za testove), dry-run, otkazivanje, jezik."""

    quarantine_dir: str
    dry_run: bool = False
    cancelled: bool = False
    lang: str = "bs"  # jezik poruka akcije (precondition/apply/verify/rollback)

    def t(self, key: str, **fmt: object) -> str:
        """Prevedi poruku akcije na jezik konteksta."""
        from mujofix.i18n.strings import tr

        return tr(key, self.lang, **fmt)


@dataclass
class ActionResult:
    action: str
    ok: bool
    verified: bool
    rolled_back: bool
    message: str
    duration_s: float = 0.0
    state: dict | None = None  # snapshot uspjesnog koraka (za "Ponisti sve")
    dry_run: bool = False  # probni mod: nista nije mijenjano


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
    """Premjesti fajl u karantin (ne trajno brisanje). Vrati zapis za manifest.

    `size` se pamti PRIJE premjestanja — bez toga se ne moze posteno reci
    koliko je premjesteno/oslobodjeno.
    """
    os.makedirs(quarantine_dir, exist_ok=True)
    base = os.path.basename(path)
    try:
        size = os.path.getsize(path)
    except OSError:
        size = 0
    dest = os.path.join(quarantine_dir, f"{int(time.time())}_{base}")
    shutil.move(path, dest)
    return {"original": path, "quarantined": dest, "size": size}


def restore_quarantined(record: dict) -> None:
    """Vrati fajl iz karantina na originalnu putanju (idempotentno)."""
    dest, original = record["quarantined"], record["original"]
    if os.path.exists(original) or not os.path.exists(dest):
        return
    os.makedirs(os.path.dirname(original), exist_ok=True)
    shutil.move(dest, original)


def quarantine_usage(quarantine_dir: str) -> tuple[int, int]:
    """(broj fajlova, bajtova) trenutno u karantinu. (0, 0) ako ne postoji."""
    files = 0
    total = 0
    if not os.path.isdir(quarantine_dir):
        return 0, 0
    for name in os.listdir(quarantine_dir):
        path = os.path.join(quarantine_dir, name)
        if not os.path.isfile(path):
            continue
        files += 1
        try:
            total += os.path.getsize(path)
        except OSError:
            pass
    return files, total


def load_quarantine_index(quarantine_dir: str) -> dict[str, str]:
    """Mapa `ime fajla u karantinu -> originalna putanja` (iz manifesta).

    Manifesti (`<akcija>-manifest.json`) se pisu pri svakom apply-u; bez njih se
    ne moze znati odakle je fajl dosao, pa se takav fajl moze samo obrisati.
    """
    index: dict[str, str] = {}
    if not os.path.isdir(quarantine_dir):
        return index
    for name in os.listdir(quarantine_dir):
        if not name.endswith("-manifest.json"):
            continue
        try:
            with open(os.path.join(quarantine_dir, name), encoding="utf-8") as h:
                records = json.load(h)
        except (OSError, json.JSONDecodeError):
            continue
        for record in records if isinstance(records, list) else []:
            quarantined = record.get("quarantined")
            original = record.get("original")
            if quarantined and original:
                index[os.path.basename(quarantined)] = original
    return index


def list_quarantine(quarantine_dir: str) -> list[dict]:
    """Fajlovi u karantinu: ime, putanja, velicina, vrijeme, originalna putanja."""
    if not os.path.isdir(quarantine_dir):
        return []
    index = load_quarantine_index(quarantine_dir)
    entries: list[dict] = []
    for name in os.listdir(quarantine_dir):
        path = os.path.join(quarantine_dir, name)
        if not os.path.isfile(path) or name.endswith("-manifest.json"):
            continue
        try:
            size, mtime = os.path.getsize(path), os.path.getmtime(path)
        except OSError:
            continue
        entries.append({"name": name, "path": path, "size": size,
                        "mtime": mtime, "original": index.get(name)})
    return sorted(entries, key=lambda entry: entry["mtime"], reverse=True)


def restore_quarantine_file(quarantine_dir: str, name: str) -> str:
    """Vrati jedan fajl iz karantina na originalnu putanju; vrati tu putanju.

    Za razliku od `restore_quarantined` (tihi, idempotentan, za rollback), ova
    funkcija DIZE OSError sa razlogom kada se ne moze vratiti — GUI to prikaze.
    """
    original = load_quarantine_index(quarantine_dir).get(name)
    if not original:
        raise OSError(
            "originalna putanja nije poznata (nema manifesta za taj fajl)")
    source = os.path.join(quarantine_dir, name)
    if not os.path.isfile(source):
        raise OSError("fajl nije u karantinu")
    if os.path.exists(original):
        raise OSError(f"na originalnoj putanji vec postoji fajl: {original}")
    parent = os.path.dirname(original)
    if parent:
        os.makedirs(parent, exist_ok=True)
    shutil.move(source, original)
    return original


def purge_quarantine(quarantine_dir: str) -> tuple[int, int]:
    """Trajno obrisi sadrzaj karantina (fajlove i manifeste).

    Vraca (broj obrisanih fajlova, oslobodjeni bajtovi). Ovo je JEDINO mjesto
    gdje se karantin trajno brise — poziva se iz GUI-ja uz potvrdu korisnika.
    """
    files = 0
    freed = 0
    if not os.path.isdir(quarantine_dir):
        return 0, 0
    for name in os.listdir(quarantine_dir):
        path = os.path.join(quarantine_dir, name)
        if not os.path.isfile(path):
            continue
        try:
            size = os.path.getsize(path)
            os.remove(path)
        except OSError:
            continue
        files += 1
        freed += size
    return files, freed



def save_manifest(quarantine_dir: str, name: str, records: list[dict]) -> str:
    path = os.path.join(quarantine_dir, f"{name}.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(records, handle, indent=2)
    return path


def action_text(action: "Action", field: str, lang: str) -> str:
    """Opis/rizik akcije na jeziku `lang` (klasa drzi kanonski tekst kao fallback).

    `description`/`risk` su klasni atributi, pa ne mogu zvati `self.t`; zato se
    prikazuje preko i18n kljuca `act_<ime>_<polje>`, a ako kljuca nema vrati se
    tekst iz klase (nikad prazno).
    """
    from mujofix.i18n.strings import tr

    key = f"act_{action.name}_{field}"
    text = tr(key, lang)
    return getattr(action, field) if text == key else text


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
            self._log(name, "cancelled", False, ctx.t("act_cancelled"))
            return ActionResult(name, False, False, False,
                                ctx.t("act_cancelled"), 0.0)
        if ctx.dry_run:
            ok, reason = action.precondition(ctx)
            self._log(name, "dry-run", ok, f"precondition: {reason}")
            return ActionResult(name, ok, False, False,
                                ctx.t("act_dry_run", r=reason), 0.0,
                                dry_run=True)
        ok, reason = action.precondition(ctx)
        if not ok:
            self._log(name, "precondition", False, reason)
            return ActionResult(name, False, False, False,
                                ctx.t("act_precondition_failed", r=reason),
                                time.time() - started)
        try:
            state = action.snapshot(ctx)
        except Exception as exc:
            self._log(name, "snapshot", False, str(exc))
            return ActionResult(name, False, False, False,
                                ctx.t("act_snapshot_failed", e=exc),
                                time.time() - started)
        try:
            action.apply(ctx, state)
        except Exception as exc:
            self._rollback_quietly(action, ctx, state)
            self._log(name, "apply", False, str(exc))
            return ActionResult(name, False, False, True,
                                ctx.t("act_apply_failed", e=exc),
                                time.time() - started)
        verified, details = action.verify(ctx, state)
        if not verified:
            self._rollback_quietly(action, ctx, state)
            self._log(name, "verify", False, details)
            return ActionResult(name, False, False, True,
                                ctx.t("act_verify_failed", d=details),
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

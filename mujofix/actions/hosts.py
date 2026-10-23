"""Akcija: ukloni sumnjiv zapis iz hosts fajla (DNS hijack).

Rizik: SREDNJI — hosts fajl je zastita DNS-a; mijenjamo ga, ali snapshot cuva
CIJELI originalni sadrzaj i rollback ga vraca bajt-identicno. Uklanjamo samo
tacno onaj zapis (ip + ime) koji je scanner prijavio; sve ostalo (komentari,
prazni redovi, ostali zapisi) ostaje netaknuto.

Elevacija: hosts fajl je na Windowsu zastita od strane sistema
(`C:\\Windows\\System32\\drivers\\etc\\hosts`), pa akcija nosi
`needs_elevation` — bez admina se preskace (postojeci UAC obrazac).
"""

from __future__ import annotations

import os
import shutil
import tempfile

from mujofix.actions.base import Action, ActionContext, register


def _read_lines(path: str) -> list[bytes]:
    """Linije kao BAJTOVI, sa svojim terminatorima (CRLF/LF ostaju tacni).

    Rad nad bajtovima (ne tekstom) je namjeran: `hosts` na Windowsu je CRLF, a
    mi obecavamo da rollback vraca fajl BAJT-identicno — tekstualni read/write bi
    pretvorio CRLF u LF i (uz ne-ASCII sadrzaj) promijenio enkodiranje.
    """
    with open(path, "rb") as handle:
        return handle.read().splitlines(keepends=True)


def _write_lines(path: str, lines: list[bytes]) -> None:
    """Upisi hosts fajl (bajt-identicno osim uklonjenih linija).

    Primarno atomski (temp u istom folderu + `os.replace`). Neke hardenovane
    Windows masine (enterprise WDAC/ASR politike) ZABRANJUJU
    MOVEFILE_REPLACE_EXISTING nad postojecim fajlom u `etc` direktoriju, ali
    dozvoljavaju kopiju preko njega — dokazano na Win11 Enterprise N:
      os.replace -> WinError 5 (Access is denied); shutil.copyfile -> OK
    Zato fallback na kopiju (nije atomska, ali je jedini put na takvim masinama).
    """
    directory = os.path.dirname(path) or "."
    handle = tempfile.NamedTemporaryFile("wb", dir=directory, delete=False)
    try:
        handle.write(b"".join(lines))
        handle.close()
        try:
            os.replace(handle.name, path)
        except OSError:
            # ponytail: kopija nije atomska; atomski replace ostaje primarni put
            shutil.copyfile(handle.name, path)
            os.unlink(handle.name)
    except Exception:
        try:
            handle.close()
            os.unlink(handle.name)
        except OSError:
            pass
        raise


def _matches(line: bytes | str, ip: str, host: str) -> bool:
    """Da li je linija tacno zapis `ip host` (ignorise komentar iza #)."""
    if isinstance(line, bytes):
        line = line.decode("utf-8", errors="replace")
    body = line.split("#", 1)[0].strip()
    if not body:
        return False
    parts = body.split()
    if len(parts) < 2:
        return False
    return parts[0] == ip and host in parts[1:]


@register
class RemoveHostsEntry(Action):
    name = "remove_hosts_entry"
    description = "Uklanjamo sumnjiv zapis iz hosts fajla (vracamo po potrebi)."
    risk = "srednji: hosts je zastita DNS-a; snapshot cuva cijeli fajl, rollback ga vraca"
    needs_elevation = True

    def __init__(self, path: str, ip: str, host: str):
        self.path = path
        self.ip = ip
        self.host = host

    def precondition(self, ctx: ActionContext) -> tuple[bool, str]:
        if not os.path.isfile(self.path):
            return False, ctx.t("act_hosts_no_file", p=self.path)
        try:
            lines = _read_lines(self.path)
        except OSError as exc:
            return False, ctx.t("act_hosts_unreadable", e=exc)
        if not any(_matches(line, self.ip, self.host) for line in lines):
            return False, ctx.t("act_hosts_not_found", ip=self.ip,
                                host=self.host)
        return True, ctx.t("act_hosts_ready", ip=self.ip, host=self.host)

    def snapshot(self, ctx: ActionContext) -> dict:
        lines = _read_lines(self.path)
        if not any(_matches(line, self.ip, self.host) for line in lines):
            raise RuntimeError(ctx.t("act_hosts_gone", ip=self.ip,
                                     host=self.host))
        return {"path": self.path, "lines": lines,
                "removed": [line for line in lines
                            if _matches(line, self.ip, self.host)]}

    def apply(self, ctx: ActionContext, state: dict) -> None:
        kept = [line for line in state["lines"]
                if not _matches(line, self.ip, self.host)]
        _write_lines(self.path, kept)

    def verify(self, ctx: ActionContext, state: dict) -> tuple[bool, str]:
        lines = _read_lines(self.path)
        if any(_matches(line, self.ip, self.host) for line in lines):
            return False, ctx.t("act_hosts_still", ip=self.ip, host=self.host)
        expected = [line for line in state["lines"]
                    if not _matches(line, self.ip, self.host)]
        if lines != expected:
            return False, ctx.t("act_hosts_changed")
        return True, ctx.t("act_hosts_done", n=len(state["removed"]),
                           ip=self.ip, host=self.host)

    def rollback(self, ctx: ActionContext, state: dict) -> None:
        _write_lines(self.path, state["lines"])

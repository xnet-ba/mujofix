"""Dnevnik izvrsavanja (audit trail) kao JSON fajl — za podrsku i dokaz.

Cist modul (bez Qt-a i bez platformskih poziva): GUI ga zove poslije popravke,
a `Runner.audit` (faze precondition/snapshot/apply/verify/dry-run) je ulaz.
Namjerno NE pise u fajl bez pozivaoca — putanju bira GUI (LOCALAPPDATA).
"""

from __future__ import annotations

import json
import os
import time


def audit_path(directory: str, when: float | None = None,
               suffix: str = "") -> str:
    """`<directory>/audit-YYYYmmdd-HHMMSS[-suffix].json`.

    `suffix` razdvaja zapise koji mogu pasti u istoj sekundi (npr. popravka i
    ciscenje karantina) da jedan ne pregazi drugi.
    """
    stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime(when or time.time()))
    tail = f"-{suffix}" if suffix else ""
    return os.path.join(directory, f"audit-{stamp}{tail}.json")


def build_record(entries: list[dict], summary: dict, dry_run: bool,
                 when: float | None = None) -> dict:
    """Zapis jednog izvrsavanja: kad, mod, sazetak i sve faze koraka."""
    return {
        "when": time.strftime("%Y-%m-%dT%H:%M:%S",
                             time.localtime(when or time.time())),
        "mode": "dry-run" if dry_run else "apply",
        "summary": dict(summary),
        "steps": [dict(entry) for entry in entries],
    }


def write_record(path: str, record: dict) -> str:
    """Upisi zapis kao citljiv JSON (UTF-8, indent 2)."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2, ensure_ascii=False)
    return path

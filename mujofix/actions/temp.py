"""Akcija: ocisti temp (fajlove starije od N dana seli u karantin).

Rizik: NIZAK — nista se ne brise trajno, karantin 30 dana, rollback vraca.
Ponistavanje: rollback vraca fajlove iz karantina na originalne putanje.
"""

from __future__ import annotations

import os
import time

from mujofix.actions.base import (
    Action,
    ActionContext,
    register,
    restore_quarantined,
    save_manifest,
    quarantine_file,
)

DEFAULT_OLDER_THAN_DAYS = 7


@register
class CleanTemp(Action):
    name = "clean_temp"
    description = "Selimo stare privremene fajlove u karantin (30 dana)."
    risk = "nizak: karantin, ne trajno brisanje; rollback vraca sve"

    def __init__(self, directory: str, older_than_days: int = DEFAULT_OLDER_THAN_DAYS):
        self.directory = directory
        self.older_than_days = older_than_days

    def _candidates(self) -> list[str]:
        cutoff = time.time() - self.older_than_days * 86400
        found: list[str] = []
        for root, _dirs, files in os.walk(self.directory):
            for name in files:
                path = os.path.join(root, name)
                try:
                    if os.path.getmtime(path) < cutoff:
                        found.append(path)
                except OSError:
                    pass
        return sorted(found)

    def precondition(self, ctx: ActionContext) -> tuple[bool, str]:
        if not os.path.isdir(self.directory):
            return False, f"folder ne postoji: {self.directory}"
        count = len(self._candidates())
        if count == 0:
            return False, "nema fajlova starijih od "\
                          f"{self.older_than_days} dana"
        return True, f"{count} fajlova za karantin"

    def snapshot(self, ctx: ActionContext) -> dict:
        return {"directory": self.directory, "files": self._candidates(),
                "records": []}

    def apply(self, ctx: ActionContext, state: dict) -> None:
        records = [quarantine_file(p, ctx.quarantine_dir)
                   for p in state["files"] if os.path.exists(p)]
        state["records"] = records
        save_manifest(ctx.quarantine_dir, f"{self.name}-manifest", records)

    def verify(self, ctx: ActionContext, state: dict) -> tuple[bool, str]:
        left = [p for p in state["files"] if os.path.exists(p)]
        if not left:
            return True, f"ocisceno {len(state['records'])} fajlova"
        return False, f"ostalo {len(left)} fajlova na mjestu"

    def rollback(self, ctx: ActionContext, state: dict) -> None:
        for record in state.get("records", []):
            restore_quarantined(record)

"""Akcija: visak kopija identicnih fajlova seli u karantin (jedna ostaje).

Radi samo na POTVRDJENIM grupama (`certain`) — one su pune sha256, ne
"vjerovatno". Nikad ne brisemo: visak ide u karantin, prva kopija ostaje.
Ponistavanje: rollback vraca sve iz karantina na originalne putanje.
"""

from __future__ import annotations

import os

from mujofix.actions.base import (
    Action,
    ActionContext,
    quarantine_file,
    register,
    restore_quarantined,
    save_manifest,
)


def _certain_groups(groups: list[dict]) -> list[dict]:
    return [g for g in groups
            if g.get("certain") and len(g.get("paths", [])) >= 2]


@register
class QuarantineDuplicates(Action):
    name = "quarantine_duplicates"
    description = "Visak identicnih kopija selimo u karantin (jedna ostaje)."
    risk = "srednji: prva kopija ostaje, ostale u karantin; rollback vraca sve"

    def __init__(self, groups: list[dict]):
        self.groups = _certain_groups(groups)

    def _victims(self) -> list[dict]:
        victims: list[dict] = []
        for group in self.groups:
            paths = group.get("paths", [])
            keep, rest = paths[0], paths[1:]
            if not os.path.exists(keep):
                continue
            for path in rest:
                if os.path.exists(path):
                    victims.append({"keep": keep, "path": path})
        return victims

    def precondition(self, ctx: ActionContext) -> tuple[bool, str]:
        victims = self._victims()
        if not victims:
            return False, ctx.t("act_dup_none")
        return True, ctx.t("act_dup_ready", n=len(victims))

    def snapshot(self, ctx: ActionContext) -> dict:
        return {"victims": self._victims(), "records": []}

    def apply(self, ctx: ActionContext, state: dict) -> None:
        records = []
        for victim in state["victims"]:
            record = quarantine_file(victim["path"], ctx.quarantine_dir)
            record["keep"] = victim["keep"]
            records.append(record)
        state["records"] = records
        save_manifest(ctx.quarantine_dir, f"{self.name}-manifest", records)

    def verify(self, ctx: ActionContext, state: dict) -> tuple[bool, str]:
        left = [r for r in state["records"] if os.path.exists(r["original"])]
        if left:
            return False, ctx.t("act_dup_left", n=len(left))
        keepers = {r["keep"] for r in state["records"]}
        gone = [k for k in keepers if not os.path.exists(k)]
        if gone:
            return False, ctx.t("act_dup_lost", p=gone[0])
        return True, ctx.t("act_dup_done", n=len(state["records"]))

    def rollback(self, ctx: ActionContext, state: dict) -> None:
        for record in state.get("records", []):
            restore_quarantined(record)

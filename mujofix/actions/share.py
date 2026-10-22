"""Akcija: ukloni nedefault mrezni share (vracamo po potrebi).

Rizik: SREDNJI — share je ulaz u racunar s mreze; uklanjanjem se zatvara, ali
snapshot pamti putanju (i remark) pa rollback vraca share tacno kako je bio.
NIKAD ne diramo administrativne share-ove (`C$`, `ADMIN$`, `IPC$`, `print$`…) —
lista je ista kao u scanneru (`DEFAULT_SHARES`), pa nema dva izvora istine.

Elevacija: `net share /delete` trazi admin, pa akcija nosi `needs_elevation` —
bez admina se preskace kroz postojeci UAC obrazac.
"""

from __future__ import annotations

import subprocess

from mujofix.actions.base import Action, ActionContext, register
from mujofix.platform import windows
from mujofix.scanners.permissions import DEFAULT_SHARES


def _run(args: list[str]) -> str:
    """Pokreni `net` i vrati stdout (patchabilno u testovima)."""
    proc = subprocess.run(["net", *args], capture_output=True, text=True,
                          timeout=30)
    if proc.returncode != 0:
        raise OSError(proc.stderr.strip() or proc.stdout.strip()
                      or f"net exit {proc.returncode}")
    return proc.stdout


def _share_info(name: str) -> dict | None:
    """(path, remark) iz `net share <ime>`; None ako share ne postoji."""
    try:
        out = _run(["share", name])
    except OSError:
        return None
    path = remark = ""
    for line in out.splitlines():
        stripped = line.strip()
        low = stripped.lower()
        if low.startswith("path"):
            path = stripped.split(None, 1)[1].strip() if " " in stripped else ""
        elif low.startswith("remark"):
            remark = stripped.split(None, 1)[1].strip() if " " in stripped else ""
        elif low.startswith("share name"):
            continue
    if not path:
        return None
    return {"path": path, "remark": remark}


@register
class RemoveShare(Action):
    name = "remove_share"
    description = "Uklanjamo mrezni share koji nisi namjerno napravio (vracamo po potrebi)."
    risk = "srednji: share se zatvara s mreze; snapshot pamti putanju i rollback ga vraca"
    needs_elevation = True

    def __init__(self, name: str, resource: str = ""):
        self.share = name
        self.resource = resource

    def precondition(self, ctx: ActionContext) -> tuple[bool, str]:
        if not windows.is_windows():
            return False, ctx.t("act_win_only")
        if self.share in DEFAULT_SHARES:
            return False, ctx.t("act_share_default", n=self.share)
        try:
            info = _share_info(self.share)
        except (OSError, subprocess.SubprocessError) as exc:
            return False, ctx.t("act_share_unreadable", e=exc)
        if info is None:
            return False, ctx.t("act_share_missing", n=self.share)
        return True, ctx.t("act_share_ready", n=self.share, p=info["path"])

    def snapshot(self, ctx: ActionContext) -> dict:
        info = _share_info(self.share)
        if info is None:
            raise RuntimeError(ctx.t("act_share_gone", n=self.share))
        return {"name": self.share, "path": info["path"],
                "remark": info["remark"]}

    def apply(self, ctx: ActionContext, state: dict) -> None:
        _run(["share", self.share, "/delete"])

    def verify(self, ctx: ActionContext, state: dict) -> tuple[bool, str]:
        if _share_info(self.share) is not None:
            return False, ctx.t("act_share_still", n=self.share)
        return True, ctx.t("act_share_done", n=self.share)

    def rollback(self, ctx: ActionContext, state: dict) -> None:
        args = ["share", f"{state['name']}={state['path']}"]
        if state.get("remark"):
            args.append(f"/remark={state['remark']}")
        _run(args)

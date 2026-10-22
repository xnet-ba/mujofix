"""Akcija: iskljuci zakazani zadatak koji se pokrece uz sistem.

Rizik: NIZAK — zadatak se ISKLJUCUJE (ne brise); snapshot pamti da je bio
ukljucen, a rollback ga vraca preko `Enable-ScheduledTask`.

Zasto PowerShell, a ne `schtasks`: prekidaci `schtasks`-a su LOKALIZOVANI na
lokalizovanom Windowsu, a cmdleti (`Get-/Disable-/Enable-ScheduledTask`) nisu.
Ime zadatka dolazi iz sistema i moze sadrzati apostrof, pa se prije ugradnje u
komandu escape-uje (inace bi bilo moguce injektovanje PowerShell koda).

Elevacija: izmjena zakazanih zadataka obicno trazi admin, pa akcija nosi
`needs_elevation` — bez admina se preskace kroz postojeci UAC obrazac.
"""

from __future__ import annotations

from mujofix.actions.base import Action, ActionContext, register
from mujofix.platform import windows
from mujofix.platform.powershell import ps_json

DISABLED = "Disabled"


def _ps_quote(text: str) -> str:
    """PowerShell single-quoted string (apostrof se duplira)."""
    return "'" + str(text).replace("'", "''") + "'"


def _ps(command: str) -> object:
    """Pokreni PowerShell (patchabilno u testovima)."""
    return ps_json(command)


def _state(task_name: str) -> str | None:
    """Stanje zadatka iz `Get-ScheduledTask` (None ako ne postoji)."""
    command = (
        f"$t = Get-ScheduledTask -TaskName {_ps_quote(task_name)} "
        "-ErrorAction SilentlyContinue; "
        "if ($t) { \"$($t.State)\" } else { \"\" }"
    )
    value = str(_ps(command) or "").strip()
    return value or None


@register
class DisableTask(Action):
    name = "disable_task"
    description = "Iskljucujemo zakazani zadatak koji se sam pokrece (vracamo po potrebi)."
    risk = "nizak: zadatak se iskljucuje, ne brise; rollback ga ponovo ukljuci"
    needs_elevation = True

    def __init__(self, task_name: str, folder: str = ""):
        self.folder = folder or "\\"
        self.task_name = task_name
        self.full_name = self._full_name()

    def _full_name(self) -> str:
        """Puno ime kako ga ocekuje Task Scheduler: '\\Folder\\Ime'."""
        folder = str(self.folder).strip().rstrip("\\")
        return f"{folder}\\{self.task_name}" if folder else f"\\{self.task_name}"

    def precondition(self, ctx: ActionContext) -> tuple[bool, str]:
        if not windows.is_windows():
            return False, ctx.t("act_win_only")
        try:
            state = _state(self.full_name)
        except Exception as exc:
            return False, ctx.t("act_task_unreadable", e=exc)
        if state is None:
            return False, ctx.t("act_task_missing", n=self.full_name)
        if state == DISABLED:
            return False, ctx.t("act_task_already", n=self.full_name)
        return True, ctx.t("act_task_ready", n=self.full_name, state=state)

    def snapshot(self, ctx: ActionContext) -> dict:
        state = _state(self.full_name)
        if state is None:
            raise RuntimeError(ctx.t("act_task_gone", n=self.full_name))
        return {"task": self.full_name, "state": state}

    def apply(self, ctx: ActionContext, state: dict) -> None:
        _ps(f"Disable-ScheduledTask -TaskName {_ps_quote(self.full_name)} "
            "| Out-Null")

    def verify(self, ctx: ActionContext, state: dict) -> tuple[bool, str]:
        if _state(self.full_name) == DISABLED:
            return True, ctx.t("act_task_done", n=self.full_name)
        return False, ctx.t("act_task_still", n=self.full_name)

    def rollback(self, ctx: ActionContext, state: dict) -> None:
        _ps(f"Enable-ScheduledTask -TaskName {_ps_quote(state['task'])} "
            "| Out-Null")

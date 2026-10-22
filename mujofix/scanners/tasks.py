"""Tasks scanner: zakazani zadaci koji se pokrecu uz sistem (Task Scheduler).

Zasto: Task Scheduler je cesto mjesto perzistencije (program se pokrece pri
prijavi/boot-u), a dosad ga nijedan scanner nije gledao.

Iskrenost: nalaz kaze CINJENICU (zadatak se pokrece uz sistem i program mu je
izvan sistemskih foldera) + razloge; nikad ne tvrdi da je virus. Citanje ide
preko PowerShell objekata (JSON) jer su `schtasks` ispisi lokalizovani.
"""

from __future__ import annotations

import os

from mujofix.core.models import Finding
from mujofix.platform import windows
from mujofix.platform.powershell import ps_json
from mujofix.scanners.base import ScanContext, Scanner, register

# Folderi u kojima program smije biti bez iznenadjenja.
TRUSTED_DIRS = (
    r"c:\windows",
    r"c:\program files",
    r"c:\program files (x86)",
    r"%systemroot%",
    r"%programfiles%",
)

# CIM klase okidaca koje znace "pokrece se uz sistem" (nezavisno od jezika).
AUTOSTART_TRIGGERS = (
    "MSFT_TaskLogonTrigger",
    "MSFT_TaskBootTrigger",
    "MSFT_TaskStartupTrigger",
)

_PS_TASKS_CMD = (
    "Get-ScheduledTask | ForEach-Object { $t = $_; "
    "[pscustomobject]@{ "
    "Name = $t.TaskName; Path = $t.TaskPath; State = \"$($t.State)\"; "
    "Triggers = @($t.Triggers | ForEach-Object { $_.CimClass.CimClassName }); "
    "Exec = @($t.Actions | ForEach-Object { \"$($_.Execute)\" }) } } | "
    "ConvertTo-Json -Depth 4"
)


def _tasks() -> list[dict]:
    data = ps_json(_PS_TASKS_CMD)
    if isinstance(data, list):
        return [t for t in data if isinstance(t, dict)]
    return [data] if isinstance(data, dict) else []


def _autostart(triggers: object) -> str | None:
    """Vrati klasu okidaca ako se zadatak pokrece uz sistem, inace None."""
    if isinstance(triggers, str):
        triggers = [triggers]
    for trigger in triggers or []:
        if trigger in AUTOSTART_TRIGGERS:
            return str(trigger)
    return None


def _untrusted_exec(execs: object) -> str | None:
    """Vrati prvu putanju programa izvan sistemskih foldera (None ako su sve)."""
    if isinstance(execs, str):
        execs = [execs]
    for raw in execs or []:
        text = str(raw or "").strip().strip('"')
        if not text:
            continue
        lowered = os.path.expandvars(text).lower()
        if lowered.startswith(TRUSTED_DIRS):
            continue
        return text
    return None


@register
class TasksScanner(Scanner):
    name = "tasks"

    def is_available(self) -> bool:
        return windows.is_windows()

    def unavailable_reason(self) -> str:
        return self.t("sc_tasks_unavailable")

    def _scan(self, ctx: ScanContext) -> list[Finding]:
        risky: list[dict] = []
        for task in _tasks():
            if ctx.cancelled:
                return []
            trigger = _autostart(task.get("Triggers"))
            if not trigger:
                continue
            program = _untrusted_exec(task.get("Exec"))
            if not program:
                continue
            risky.append({
                "name": str(task.get("Name", "")),
                "folder": str(task.get("Path", "")),
                "trigger": trigger,
                "program": program,
                "state": str(task.get("State", "")),
            })
        if not risky:
            return []
        severity = "MEDIUM" if len(risky) >= 3 else "LOW"
        return [Finding(
            id="tasks-autostart-untrusted",
            scanner=self.name,
            title=self.t("sc_tasks_title", n=len(risky)),
            why=self.t("sc_tasks_why"),
            severity=severity,
            impact=self.t("sc_tasks_impact"),
            risk=self.t("sc_tasks_risk"),
            reversible=True,
            evidence={"count": len(risky), "tasks": risky[:20]},
            tech_details=self.t("sc_tasks_tech"),
        )]

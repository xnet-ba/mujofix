"""Akcija: restartuj servis (samo Windows, treba UAC elevaciju).

Rizik: SREDNJI — restart prekida funkciju servisa na kratko; ako je uzrok
rusenja i dalje prisutan, servis ce opet stati (verify to hvata -> rollback).
Ponistavanje: rollback vraca prethodno stanje (Running/Stopped).

Koristi `sc` (stdlib subprocess, bez pywin32). Netestirano na Win10/11.
"""

from __future__ import annotations

import re
import subprocess
import time

from mujofix.actions.base import Action, ActionContext, register
from mujofix.platform import windows

VERIFY_TIMEOUT_S = 30


def _sc(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["sc", *args], capture_output=True,
                          text=True, timeout=60)


def _state(service: str) -> str | None:
    """RUNNING / STOPPED / ... ili None ako servis ne postoji."""
    proc = _sc("query", service)
    if proc.returncode != 0:
        return None
    match = re.search(r"STATE\s*:\s*\d+\s+(\w+)", proc.stdout)
    return match.group(1) if match else None


@register
class RestartService(Action):
    name = "restart_service"
    description = "Gasimo pa palimo servis koji je stao."
    risk = ("srednji: kratki prekid funkcije servisa; ako se opet srusi, "
            "verify pada i stanje se vraca")
    needs_elevation = True

    def __init__(self, service: str):
        self.service = service

    def precondition(self, ctx: ActionContext) -> tuple[bool, str]:
        if not windows.is_windows():
            return False, ctx.t("act_win_only")
        state = _state(self.service)
        if state is None:
            return False, ctx.t("act_svc_missing", s=self.service)
        return True, ctx.t("act_svc_exists", s=self.service, state=state)

    def snapshot(self, ctx: ActionContext) -> dict:
        state = _state(self.service)
        if state is None:
            raise RuntimeError(ctx.t("act_svc_gone", s=self.service))
        return {"service": self.service, "was": state}

    def apply(self, ctx: ActionContext, state: dict) -> None:
        _sc("stop", state["service"])
        proc = _sc("start", state["service"])
        if proc.returncode != 0:
            raise RuntimeError(ctx.t("act_svc_start_failed",
                                     e=proc.stderr.strip()[-200:]))

    def verify(self, ctx: ActionContext, state: dict) -> tuple[bool, str]:
        # Servis nakon starta prolazi kroz START_PENDING; cekamo RUNNING.
        # Bez cekanja verify lazno pada (ulovljeno na pravom hostu).
        deadline = time.time() + VERIFY_TIMEOUT_S
        now = _state(state["service"])
        while now != "RUNNING" and time.time() < deadline:
            time.sleep(1)
            now = _state(state["service"])
        if now == "RUNNING":
            return True, ctx.t("act_svc_running", s=state["service"])
        return False, ctx.t("act_svc_state", s=state["service"], now=now)

    def rollback(self, ctx: ActionContext, state: dict) -> None:
        if state["was"] == "RUNNING":
            _sc("start", state["service"])
        else:
            _sc("stop", state["service"])

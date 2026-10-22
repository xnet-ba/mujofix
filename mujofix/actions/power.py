"""Akcija: prebaci aktivni plan napajanja sa "Power Saver" na "Balanced".

Rizik: NIZAK — mijenja se samo AKTIVNI plan; snapshot pamti prijasnji GUID i
rollback ga vraca preko `powercfg /setactive`. Ne dira se nijedna postavka
planova (nista se ne brise, ne mijenja se sadrzaj seme).

GUID za "Balanced" (dokazan iz primarnog izvora, ne po pamcenju):
Microsoft, "Powercfg command-line options" — primjer za `/changename` koristi
tacno `381b4222-f694-41f0-9685-ff5bb260df2e` uz ime "Customized Balanced".
https://learn.microsoft.com/en-us/windows-hardware/design/device-experiences/powercfg-command-line-options
(provjereno 2026-10-22).

Napomena o elevaciji: `powercfg /setactive` je po korisniku, pa akcija NE trazi
elevaciju; ako okruzenje ipak trazi admin, apply padne i Runner vrati stanje
(bez lazne tvrdnje da je uspjelo).
"""

from __future__ import annotations

import re
import subprocess

from mujofix.actions.base import Action, ActionContext, register
from mujofix.platform import windows

BALANCED_GUID = "381b4222-f694-41f0-9685-ff5bb260df2e"
GUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
                     r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")


def _run(args: list[str]) -> str:
    """Pokreni `powercfg` i vrati stdout (patchabilno u testovima)."""
    proc = subprocess.run(["powercfg", *args], capture_output=True, text=True,
                          timeout=30)
    if proc.returncode != 0:
        raise OSError(proc.stderr.strip() or f"powercfg exit {proc.returncode}")
    return proc.stdout


def active_guid() -> str | None:
    """GUID aktivnog plana iz `powercfg /getactivescheme` (None ako ne radi)."""
    match = GUID_RE.search(_run(["/getactivescheme"]))
    return match.group(0).lower() if match else None


@register
class DisablePowerSaver(Action):
    name = "disable_power_saver"
    description = "Vracamo plan napajanja na uravnotezeni (Balanced)."
    risk = "nizak: mijenja se samo aktivni plan; snapshot pamti stari GUID i rollback ga vraca"

    def precondition(self, ctx: ActionContext) -> tuple[bool, str]:
        if not windows.is_windows():
            return False, ctx.t("act_win_only")
        try:
            current = active_guid()
        except (OSError, subprocess.SubprocessError) as exc:
            return False, ctx.t("act_power_unreadable", e=exc)
        if not current:
            return False, ctx.t("act_power_unreadable", e="nema GUID-a u izlazu")
        if current == BALANCED_GUID:
            return False, ctx.t("act_power_already")
        return True, ctx.t("act_power_ready", guid=current)

    def snapshot(self, ctx: ActionContext) -> dict:
        current = active_guid()
        if not current:
            raise RuntimeError(ctx.t("act_power_gone"))
        return {"scheme": current}

    def apply(self, ctx: ActionContext, state: dict) -> None:
        _run(["/setactive", BALANCED_GUID])

    def verify(self, ctx: ActionContext, state: dict) -> tuple[bool, str]:
        current = active_guid()
        if current == BALANCED_GUID:
            return True, ctx.t("act_power_done")
        return False, ctx.t("act_power_still", guid=current or "?")

    def rollback(self, ctx: ActionContext, state: dict) -> None:
        _run(["/setactive", state["scheme"]])

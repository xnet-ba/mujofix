"""Akcija: iskljuci sistemski proxy (HKCU Internet Settings).

Rizik: NIZAK — gasimo ProxyEnable i cuvamo staru vrijednost za rollback.
Ponistavanje: rollback vraca tacan ProxyEnable (i tip) nazad.
"""

from __future__ import annotations

from mujofix.actions import env
from mujofix.actions.base import Action, ActionContext, register
from mujofix.platform import windows

INTERNET_SETTINGS = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"


@register
class DisableProxy(Action):
    name = "disable_proxy"
    description = "Iskljucujemo proxy za internet promet (vracamo po potrebi)."
    risk = "nizak: cuvamo ProxyEnable, rollback ga vraca"

    def precondition(self, ctx: ActionContext) -> tuple[bool, str]:
        if not windows.is_windows():
            return False, ctx.t("act_win_only")
        enabled, _kind = env.read_env("HKCU", INTERNET_SETTINGS, "ProxyEnable")
        if str(enabled) != "1":
            return False, ctx.t("act_proxy_not_on")
        return True, ctx.t("act_proxy_on")

    def snapshot(self, ctx: ActionContext) -> dict:
        enabled, kind = env.read_env("HKCU", INTERNET_SETTINGS, "ProxyEnable")
        if str(enabled) != "1":
            raise RuntimeError(ctx.t("act_proxy_changed"))
        return {"value": enabled, "kind": kind}

    def apply(self, ctx: ActionContext, state: dict) -> None:
        env.write_env("HKCU", INTERNET_SETTINGS, "ProxyEnable", 0, "dword")

    def verify(self, ctx: ActionContext, state: dict) -> tuple[bool, str]:
        enabled, _kind = env.read_env("HKCU", INTERNET_SETTINGS, "ProxyEnable")
        if str(enabled) == "0":
            return True, ctx.t("act_proxy_done")
        return False, ctx.t("act_proxy_still_on", e=enabled)

    def rollback(self, ctx: ActionContext, state: dict) -> None:
        env.write_env("HKCU", INTERNET_SETTINGS, "ProxyEnable",
                      state["value"], state["kind"])

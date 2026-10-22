"""Akcije za Environment varijable (registry): mrtvi PATH unosi i TEMP/TMP.

Rizik: NIZAK — mijenjamo jednu vrijednost i cuvamo tacan original (vrijednost
+ registry tip) za rollback. HKCU prolazi bez UAC-a; HKLM PATH trazi elevaciju.
Ponistavanje: rollback upisuje original nazad, pa se javlja promjena okoline.
"""

from __future__ import annotations

import ctypes
import os

from mujofix.actions.base import Action, ActionContext, register
from mujofix.platform import windows

USER_ENV = r"Environment"  # HKCU
SYSTEM_ENV = r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
SEP = ";"
DEFAULT_TEMP = r"%USERPROFILE%\AppData\Local\Temp"


def _hkey(hive: str):
    import winreg

    return {"HKCU": winreg.HKEY_CURRENT_USER, "HKLM": winreg.HKEY_LOCAL_MACHINE}[hive]


def read_env(hive: str, key: str, name: str) -> tuple[object | None, int]:
    """(vrijednost, registry tip); (None, REG_SZ) ako vrijednost ne postoji."""
    if not windows.is_windows():
        raise windows.NotSupported("registry postoji samo na Windowsu")
    import winreg

    try:
        with winreg.OpenKey(_hkey(hive), key) as handle:
            value, kind = winreg.QueryValueEx(handle, name)
            return value, kind
    except FileNotFoundError:
        return None, winreg.REG_SZ


_KINDS = {"sz": "REG_SZ", "expand_sz": "REG_EXPAND_SZ", "dword": "REG_DWORD"}


def write_env(hive: str, key: str, name: str, value, kind=None) -> None:
    """kind: int (raw tip iz read_env), ime ("sz"/"expand_sz"/"dword") ili None."""
    import winreg

    if isinstance(kind, str):
        kind = getattr(winreg, _KINDS.get(kind, "REG_SZ"))
    elif kind is None:
        kind = winreg.REG_SZ
    with winreg.OpenKey(_hkey(hive), key, 0, winreg.KEY_SET_VALUE) as handle:
        winreg.SetValueEx(handle, name, 0, kind, value)
    broadcast_env_change()


def _delete_env(hive: str, key: str, name: str) -> None:
    import winreg

    with winreg.OpenKey(_hkey(hive), key, 0, winreg.KEY_SET_VALUE) as handle:
        winreg.DeleteValue(handle, name)
    broadcast_env_change()


def broadcast_env_change() -> None:
    """Javi pokrenutim programima da je okolina promijenjena (bezopasno)."""
    try:
        result = ctypes.c_long()
        ctypes.windll.user32.SendMessageTimeoutW(
            0xFFFF, 0x1A, 0, ctypes.c_wchar_p("Environment"), 0x0002, 5000,
            ctypes.byref(result))
    except Exception:
        pass


def _resolve_hive(entry: str) -> tuple[str, str] | None:
    """Gdje PATH (HKCU prvo) sadrzi ovaj unos: (hive, key) ili None."""
    target = entry.strip().lower()
    if not target:
        return None
    for hive, key in (("HKCU", USER_ENV), ("HKLM", SYSTEM_ENV)):
        try:
            value, _kind = read_env(hive, key, "Path")
        except windows.NotSupported:
            return None
        if value and target in [p.strip().lower() for p in str(value).split(SEP)]:
            return hive, key
    return None


@register
class RemovePathEntry(Action):
    name = "remove_path_entry"
    description = "Uklanjamo mrtvi unos iz PATH varijable."
    risk = "nizak: stara vrijednost se cuva, rollback vraca tacno"

    def __init__(self, entry: str):
        self.entry = entry
        found = _resolve_hive(entry)
        self._found = found is not None
        self.hive = found[0] if found else "HKCU"
        self.key = found[1] if found else USER_ENV
        self.needs_elevation = self.hive == "HKLM"

    def precondition(self, ctx: ActionContext) -> tuple[bool, str]:
        if not windows.is_windows():
            return False, ctx.t("act_win_only")
        if not self.entry.strip():
            return False, ctx.t("act_env_empty")
        found = _resolve_hive(self.entry)
        if not found:
            return False, ctx.t("act_env_not_in_path", e=self.entry)
        self.hive, self.key = found
        self.needs_elevation = self.hive == "HKLM"
        return True, ctx.t("act_env_dead_entry", h=self.hive, e=self.entry)

    def snapshot(self, ctx: ActionContext) -> dict:
        value, kind = read_env(self.hive, self.key, "Path")
        if value is None:
            raise RuntimeError(ctx.t("act_env_path_gone"))
        return {"hive": self.hive, "key": self.key, "value": str(value),
                "kind": kind, "entry": self.entry}

    def apply(self, ctx: ActionContext, state: dict) -> None:
        target = state["entry"].strip().lower()
        kept = [p for p in state["value"].split(SEP)
                if p.strip().lower() != target]
        write_env(state["hive"], state["key"], "Path", SEP.join(kept),
                  state["kind"])

    def verify(self, ctx: ActionContext, state: dict) -> tuple[bool, str]:
        value, _kind = read_env(state["hive"], state["key"], "Path")
        if value is None:
            return False, ctx.t("act_env_path_unreadable")
        target = state["entry"].strip().lower()
        left = [p for p in str(value).split(SEP) if p.strip().lower() == target]
        if left:
            return False, ctx.t("act_env_still_in_path", e=state["entry"])
        return True, ctx.t("act_env_removed")

    def rollback(self, ctx: ActionContext, state: dict) -> None:
        write_env(state["hive"], state["key"], "Path", state["value"],
                  state["kind"])


@register
class FixTempVar(Action):
    name = "fix_temp_var"
    description = "Vracamo TEMP/TMP na ispravan privremeni folder."
    risk = "nizak: stara vrijednost se cuva, rollback vraca tacno"

    def __init__(self, var: str, target: str | None = None):
        self.var = var.strip().upper()
        self.target = target or os.path.expandvars(DEFAULT_TEMP)

    def precondition(self, ctx: ActionContext) -> tuple[bool, str]:
        if not windows.is_windows():
            return False, ctx.t("act_win_only")
        if self.var not in ("TEMP", "TMP"):
            return False, ctx.t("act_env_unknown_var", v=self.var or "?")
        current, _kind = read_env("HKCU", USER_ENV, self.var)
        resolved = os.path.expandvars(str(current)) if current else ""
        if resolved and os.path.isdir(resolved):
            return False, ctx.t("act_env_already_ok", v=self.var, cur=current)
        return True, ctx.t("act_env_target", v=self.var, t=self.target)

    def snapshot(self, ctx: ActionContext) -> dict:
        value, kind = read_env("HKCU", USER_ENV, self.var)
        return {"var": self.var, "value": value, "kind": kind}

    def apply(self, ctx: ActionContext, state: dict) -> None:
        write_env("HKCU", USER_ENV, state["var"], self.target, "sz")

    def verify(self, ctx: ActionContext, state: dict) -> tuple[bool, str]:
        current, _kind = read_env("HKCU", USER_ENV, state["var"])
        resolved = os.path.expandvars(str(current)) if current else ""
        if resolved and os.path.isdir(resolved):
            return True, ctx.t("act_env_fixed", v=state["var"])
        return False, ctx.t("act_env_still_wrong", v=state["var"], cur=current)

    def rollback(self, ctx: ActionContext, state: dict) -> None:
        if state["value"] is None:
            _delete_env("HKCU", USER_ENV, state["var"])
            return
        write_env("HKCU", USER_ENV, state["var"], state["value"],
                  state.get("kind"))

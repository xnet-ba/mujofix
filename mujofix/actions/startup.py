"""Akcija: onemoguci startup stavku (brise Run vrijednost, rollback je vraca).

Rizik: NIZAK za HKCU (korisnicki kljuc, ponistava se jednim klikom).
Za HKLM treba UAC elevacija (needs_elevation=True).
Ponistavanje: rollback upisuje sacuvanu vrijednost nazad.
"""

from __future__ import annotations

from mujofix.actions.base import Action, ActionContext, register
from mujofix.platform import windows


def _read_value(hive: str, path: str, name: str) -> str | None:
    if not windows.is_windows():
        raise windows.NotSupported("registry postoji samo na Windowsu")
    import winreg

    hives = {"HKCU": winreg.HKEY_CURRENT_USER, "HKLM": winreg.HKEY_LOCAL_MACHINE}
    try:
        with winreg.OpenKey(hives[hive], path) as key:
            value, _kind = winreg.QueryValueEx(key, name)
            return str(value)
    except FileNotFoundError:
        return None


def _delete_value(hive: str, path: str, name: str) -> None:
    import winreg

    hives = {"HKCU": winreg.HKEY_CURRENT_USER, "HKLM": winreg.HKEY_LOCAL_MACHINE}
    with winreg.OpenKey(hives[hive], path, 0, winreg.KEY_SET_VALUE) as key:
        winreg.DeleteValue(key, name)


def _set_value(hive: str, path: str, name: str, value: str) -> None:
    import winreg

    hives = {"HKCU": winreg.HKEY_CURRENT_USER, "HKLM": winreg.HKEY_LOCAL_MACHINE}
    with winreg.OpenKey(hives[hive], path, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)


@register
class DisableStartupItem(Action):
    name = "disable_startup_item"
    description = "Onemogucavamo program da se sam pali s Windowsom."
    risk = "nizak: vrijednost se cuva i vraca jednim rollback-om"

    def __init__(self, hive: str, path: str, entry: str):
        self.hive = hive
        self.path = path
        self.entry = entry
        self.needs_elevation = hive == "HKLM"

    def precondition(self, ctx: ActionContext) -> tuple[bool, str]:
        if not windows.is_windows():
            return False, "samo Windows"
        try:
            current = _read_value(self.hive, self.path, self.entry)
        except windows.NotSupported as exc:
            return False, str(exc)
        if current is None:
            return False, f"stavka {self.entry} ne postoji (vec onemogucena?)"
        return True, f"stavka postoji: {current[:80]}"

    def snapshot(self, ctx: ActionContext) -> dict:
        value = _read_value(self.hive, self.path, self.entry)
        if value is None:
            raise RuntimeError("stavka nestala izmedju precondition i snapshot")
        return {"hive": self.hive, "path": self.path,
                "entry": self.entry, "value": value}

    def apply(self, ctx: ActionContext, state: dict) -> None:
        _delete_value(state["hive"], state["path"], state["entry"])

    def verify(self, ctx: ActionContext, state: dict) -> tuple[bool, str]:
        current = _read_value(state["hive"], state["path"], state["entry"])
        if current is None:
            return True, f"{state['entry']} vise nije u startup-u"
        return False, f"{state['entry']} je i dalje prisutna"

    def rollback(self, ctx: ActionContext, state: dict) -> None:
        _set_value(state["hive"], state["path"], state["entry"], state["value"])

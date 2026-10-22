"""Akcija `disable_task`: PowerShell se simulira (nema Windowsa u CI-ju)."""

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mujofix.actions.base import ActionContext, Runner
from mujofix.actions.mapping import finding_to_actions
from mujofix.actions.task import DisableTask

BS_CHARS = "čćžšđ"


class FakePowerShell:
    """Simulira Get-/Disable-/Enable-ScheduledTask nad dict-om stanja."""

    def __init__(self, state: dict | None = None):
        self.state = dict(state or {r"\Updater": "Ready"})
        self.commands: list[str] = []

    def __call__(self, command: str) -> object:
        self.commands.append(command)
        name = None
        for key in self.state:
            if f"'{key}'" in command or f"'{key.replace(chr(39), chr(39)*2)}'" in command:
                name = key
                break
        if name is None:  # nema takvog zadatka
            return ""
        if command.startswith("Disable-ScheduledTask"):
            self.state[name] = "Disabled"
            return ""
        if command.startswith("Enable-ScheduledTask"):
            self.state[name] = "Ready"
            return ""
        return self.state[name]


class TestDisableTask(unittest.TestCase):
    def _ctx(self, lang="bs"):
        return ActionContext(quarantine_dir="/tmp/q", lang=lang)

    def test_apply_verify_and_rollback_reenable_the_task(self):
        fake = FakePowerShell()
        with patch("mujofix.actions.task._ps", fake), \
             patch("mujofix.actions.task.windows.is_windows",
                   return_value=True):
            ctx = self._ctx()
            action = DisableTask("Updater")
            result = Runner().run(action, ctx)
            self.assertTrue(result.ok and result.verified, result.message)
            self.assertEqual(fake.state[r"\Updater"], "Disabled")
            action.rollback(ctx, result.state)
            self.assertEqual(fake.state[r"\Updater"], "Ready")
        self.assertIn("\\Updater", action.full_name)

    def test_refuses_when_already_disabled(self):
        fake = FakePowerShell({r"\Updater": "Disabled"})
        with patch("mujofix.actions.task._ps", fake), \
             patch("mujofix.actions.task.windows.is_windows",
                   return_value=True):
            ok, reason = DisableTask("Updater").precondition(self._ctx())
        self.assertFalse(ok)
        self.assertIn("vec iskljucen", reason)
        self.assertEqual(len(fake.commands), 1)  # samo citanje stanja

    def test_refuses_when_task_missing(self):
        fake = FakePowerShell({})
        with patch("mujofix.actions.task._ps", fake), \
             patch("mujofix.actions.task.windows.is_windows",
                   return_value=True):
            ok, reason = DisableTask("NemaMe").precondition(self._ctx())
        self.assertFalse(ok)
        self.assertIn("ne postoji", reason)

    def test_non_windows_is_refused(self):
        with patch("mujofix.actions.task.windows.is_windows",
                   return_value=False):
            ok, reason = DisableTask("Updater").precondition(self._ctx())
        self.assertFalse(ok)
        self.assertIn("samo Windows", reason)

    def test_powershell_failure_is_reported_not_crash(self):
        def boom(command):
            raise RuntimeError("powershell nema")

        with patch("mujofix.actions.task._ps", boom), \
             patch("mujofix.actions.task.windows.is_windows",
                   return_value=True):
            result = Runner().run(DisableTask("Updater"), self._ctx())
        self.assertFalse(result.ok)
        self.assertIn("precondition", result.message)

    def test_task_name_with_quote_is_escaped(self):
        """Ime dolazi iz sistema — apostrof ne smije injektovati PowerShell."""
        action = DisableTask("O'Brien", "\\Test")
        fake = FakePowerShell({r"\Test\O'Brien": "Ready"})
        with patch("mujofix.actions.task._ps", fake), \
             patch("mujofix.actions.task.windows.is_windows",
                   return_value=True):
            Runner().run(action, self._ctx())
        for command in fake.commands:
            if "Brien" in command:
                self.assertIn("O''Brien", command)      # escape-ovano
                self.assertNotIn("O'Brien", command)     # nikad golo

    def test_full_name_builds_scheduler_path(self):
        self.assertEqual(DisableTask("X").full_name, "\\X")
        self.assertEqual(DisableTask("X", "\\").full_name, "\\X")
        self.assertEqual(DisableTask("X", "\\Microsoft\\Windows\\Y").full_name,
                         "\\Microsoft\\Windows\\Y\\X")

    def test_needs_elevation_and_mapping(self):
        self.assertTrue(DisableTask("X").needs_elevation)
        actions = finding_to_actions({
            "id": "tasks-autostart-untrusted", "scanner": "tasks",
            "evidence": {"tasks": [{"name": "A", "folder": "\\F"},
                                   {"name": "B", "folder": "\\F"}]}})
        self.assertEqual([a.name for a in actions], ["disable_task"] * 2)
        self.assertEqual([a.full_name for a in actions], ["\\F\\A", "\\F\\B"])

    def test_messages_are_bilingual(self):
        fake = FakePowerShell()
        with patch("mujofix.actions.task._ps", fake), \
             patch("mujofix.actions.task.windows.is_windows",
                   return_value=True):
            bs = DisableTask("Updater").precondition(self._ctx("bs"))[1]
            en = DisableTask("Updater").precondition(self._ctx("en"))[1]
        self.assertIn("je ukljucen", bs)
        self.assertIn("is enabled", en)
        self.assertFalse(set(BS_CHARS) & set(en.lower()))


if __name__ == "__main__":
    unittest.main()

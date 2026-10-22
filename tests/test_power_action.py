"""Akcija `disable_power_saver`: powercfg se simulira (nema Windowsa u CI-ju)."""

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mujofix.actions.base import ActionContext, Runner
from mujofix.actions.mapping import finding_to_actions
from mujofix.actions.power import BALANCED_GUID, DisablePowerSaver

BS_CHARS = "čćžšđ"
SAVER = "a1841308-3541-4fab-bc81-f71556f20b4a"  # samo kao "neki drugi plan"


class FakePowerCfg:
    """Simulira `powercfg /getactivescheme` i `/setactive` (bez Windowsa)."""

    def __init__(self, active: str = SAVER):
        self.active = active
        self.calls: list[list[str]] = []

    def __call__(self, args: list[str]) -> str:
        self.calls.append(args)
        if args[0] == "/getactivescheme":
            return (f"Power Scheme GUID: {self.active}  (Neki plan)")
        if args[0] == "/setactive":
            self.active = args[1].lower()
            return ""
        raise AssertionError(f"neocekivan powercfg poziv: {args}")


class TestDisablePowerSaver(unittest.TestCase):
    def _ctx(self, lang="bs"):
        return ActionContext(quarantine_dir="/tmp/q", lang=lang)

    def test_apply_verify_and_rollback_restore_previous_plan(self):
        fake = FakePowerCfg(SAVER)
        with patch("mujofix.actions.power._run", fake), \
             patch("mujofix.actions.power.windows.is_windows",
                   return_value=True):
            ctx = self._ctx()
            action = DisablePowerSaver()
            result = Runner().run(action, ctx)
            self.assertTrue(result.ok and result.verified, result.message)
            self.assertEqual(fake.active, BALANCED_GUID)
            action.rollback(ctx, result.state)
            self.assertEqual(fake.active, SAVER)
        self.assertEqual(fake.calls[0], ["/getactivescheme"])
        self.assertIn(["/setactive", BALANCED_GUID], fake.calls)
        self.assertEqual(fake.calls[-1], ["/setactive", SAVER])

    def test_refuses_when_already_balanced(self):
        fake = FakePowerCfg(BALANCED_GUID)
        with patch("mujofix.actions.power._run", fake), \
             patch("mujofix.actions.power.windows.is_windows",
                   return_value=True):
            ok, reason = DisablePowerSaver().precondition(self._ctx())
        self.assertFalse(ok)
        self.assertIn("vec uravnotezen", reason)
        self.assertEqual(fake.calls, [["/getactivescheme"]])  # nista nije mijenjano

    def test_non_windows_is_refused(self):
        with patch("mujofix.actions.power.windows.is_windows",
                   return_value=False):
            ok, reason = DisablePowerSaver().precondition(self._ctx())
        self.assertFalse(ok)
        self.assertIn("samo Windows", reason)

    def test_unreadable_powercfg_is_refused_not_crash(self):
        def boom(_args):
            raise OSError("powercfg nije nadjen")

        with patch("mujofix.actions.power._run", boom), \
             patch("mujofix.actions.power.windows.is_windows",
                   return_value=True):
            result = Runner().run(DisablePowerSaver(), self._ctx())
        self.assertFalse(result.ok)
        self.assertIn("precondition", result.message)

    def test_failed_apply_rolls_back_and_reports(self):
        """Ako /setactive ne uspije, stanje se vraca i nema laznog uspjeha."""
        state = {"active": SAVER}

        def flaky(args):
            if args[0] == "/getactivescheme":
                return f"Power Scheme GUID: {state['active']}  (x)"
            if args[0] == "/setactive" and args[1] == BALANCED_GUID:
                raise OSError("pristup odbijen")
            state["active"] = args[1].lower()
            return ""

        with patch("mujofix.actions.power._run", flaky), \
             patch("mujofix.actions.power.windows.is_windows",
                   return_value=True):
            result = Runner().run(DisablePowerSaver(), self._ctx())
        self.assertFalse(result.ok)
        self.assertTrue(result.rolled_back)
        self.assertIn("apply pao", result.message)

    def test_messages_are_bilingual(self):
        fake = FakePowerCfg(SAVER)
        with patch("mujofix.actions.power._run", fake), \
             patch("mujofix.actions.power.windows.is_windows",
                   return_value=True):
            bs = DisablePowerSaver().precondition(self._ctx("bs"))[1]
            en = DisablePowerSaver().precondition(self._ctx("en"))[1]
        self.assertIn("prebacujemo na Balanced", bs)
        self.assertIn("switching to Balanced", en)
        self.assertFalse(set(BS_CHARS) & set(en.lower()))

    def test_mapping_maps_the_finding(self):
        actions = finding_to_actions(
            {"id": "config-power-saver", "scanner": "config", "evidence": {}})
        self.assertEqual([a.name for a in actions], ["disable_power_saver"])

    def test_balanced_guid_matches_the_documented_one(self):
        """GUID je iz primarnog izvora (Microsoft powercfg docs) — ne mijenjati
        bez ponovne provjere i novog citata."""
        self.assertEqual(BALANCED_GUID,
                         "381b4222-f694-41f0-9685-ff5bb260df2e")


if __name__ == "__main__":
    unittest.main()

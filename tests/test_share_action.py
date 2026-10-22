"""Akcija `remove_share`: `net` se simulira (nema Windowsa u CI-ju)."""

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mujofix.actions.base import ActionContext, Runner
from mujofix.actions.mapping import finding_to_actions
from mujofix.actions.share import RemoveShare

BS_CHARS = "čćžšđ"


class FakeNet:
    """Simulira `net share` / `net share <ime>` / `/delete` / `name=path`."""

    def __init__(self, shares: dict | None = None):
        self.shares = dict(shares or {"TestShare": (r"C:\Test", "test remark")})
        self.calls: list[list[str]] = []

    def __call__(self, args: list[str]) -> str:
        self.calls.append(args)
        if args[:1] == ["share"] and len(args) >= 2 and "=" in args[1]:
            name, path = args[1].split("=", 1)
            remark = next((a.split("=", 1)[1] for a in args[2:]
                           if a.startswith("/remark=")), "")
            self.shares[name] = (path, remark)
            return ""
        if args[:2] == ["share", "/delete"]:
            self.shares.pop(args[2], None)
            return ""
        if len(args) == 3 and args[2] == "/delete":
            if args[1] not in self.shares:
                raise OSError("share ne postoji")
            self.shares.pop(args[1])
            return ""
        if len(args) == 2:  # net share <ime>
            entry = self.shares.get(args[1])
            if entry is None:
                raise OSError("share ne postoji")
            path, remark = entry
            return (f"Share name        {args[1]}\nPath              {path}\n"
                    f"Remark            {remark}\n")
        return ""


class TestRemoveShare(unittest.TestCase):
    def _ctx(self, lang="bs"):
        return ActionContext(quarantine_dir="/tmp/q", lang=lang)

    def test_apply_verify_rollback_restores_the_share(self):
        fake = FakeNet()
        with patch("mujofix.actions.share._run", fake), \
             patch("mujofix.actions.share.windows.is_windows",
                   return_value=True):
            ctx = self._ctx()
            action = RemoveShare("TestShare", r"C:\Test")
            result = Runner().run(action, ctx)
            self.assertTrue(result.ok and result.verified, result.message)
            self.assertNotIn("TestShare", fake.shares)
            action.rollback(ctx, result.state)
            self.assertEqual(fake.shares["TestShare"], (r"C:\Test",
                                                        "test remark"))
        self.assertIn(["share", "TestShare", "/delete"], fake.calls)

    def test_never_touches_administrative_shares(self):
        fake = FakeNet({"C$": ("C:\\", "Default share")})
        with patch("mujofix.actions.share._run", fake), \
             patch("mujofix.actions.share.windows.is_windows",
                   return_value=True):
            for name in ("C$", "ADMIN$", "IPC$", "print$"):
                ok, reason = RemoveShare(name).precondition(self._ctx())
                self.assertFalse(ok, name)
                self.assertIn("sistemski", reason)
        self.assertEqual(fake.calls, [])  # ni jedan `net` poziv

    def test_refuses_when_share_missing(self):
        fake = FakeNet({})
        with patch("mujofix.actions.share._run", fake), \
             patch("mujofix.actions.share.windows.is_windows",
                   return_value=True):
            ok, reason = RemoveShare("NemaMe").precondition(self._ctx())
        self.assertFalse(ok)
        self.assertIn("ne postoji", reason)

    def test_non_windows_is_refused(self):
        with patch("mujofix.actions.share.windows.is_windows",
                   return_value=False):
            ok, reason = RemoveShare("TestShare").precondition(self._ctx())
        self.assertFalse(ok)
        self.assertIn("samo Windows", reason)

    def test_failed_delete_rolls_back_without_false_success(self):
        fake = FakeNet()
        real = fake.__call__

        def flaky(args):
            if args == ["share", "TestShare", "/delete"]:
                raise OSError("pristup odbijen")
            return real(args)

        with patch("mujofix.actions.share._run", flaky), \
             patch("mujofix.actions.share.windows.is_windows",
                   return_value=True):
            result = Runner().run(RemoveShare("TestShare"), self._ctx())
        self.assertFalse(result.ok)
        self.assertTrue(result.rolled_back)
        self.assertIn("TestShare", fake.shares)  # share je vracen

    def test_needs_elevation(self):
        self.assertTrue(RemoveShare("TestShare").needs_elevation)

    def test_messages_are_bilingual(self):
        fake = FakeNet()
        with patch("mujofix.actions.share._run", fake), \
             patch("mujofix.actions.share.windows.is_windows",
                   return_value=True):
            bs = RemoveShare("TestShare").precondition(self._ctx("bs"))[1]
            en = RemoveShare("TestShare").precondition(self._ctx("en"))[1]
        self.assertIn("vodi na", bs)
        self.assertIn("points to", en)
        self.assertFalse(set(BS_CHARS) & set(en.lower()))

    def test_mapping_creates_one_action_per_share(self):
        finding = {"id": "permissions-shares", "scanner": "permissions",
                   "evidence": {"shares": [{"name": "A", "resource": r"C:\A"},
                                           {"name": "B", "resource": r"C:\B"}]}}
        actions = finding_to_actions(finding)
        self.assertEqual([a.name for a in actions], ["remove_share"] * 2)
        self.assertEqual([a.share for a in actions], ["A", "B"])


if __name__ == "__main__":
    unittest.main()

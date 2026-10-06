"""Testovi Faze 2a: ugovor Runnera dokazan laznom akcijom (TDD baza za prave)."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mujofix.actions.base import (
    CATALOG,
    Action,
    ActionContext,
    Runner,
    quarantine_file,
    restore_quarantined,
)


class FakeAction(Action):
    """Skriptabilna akcija: ponasanje se zadaje kroz konstruktor."""

    name = "fake"

    def __init__(self, fail_at: str | None = None):
        self.fail_at = fail_at  # None|precondition|snapshot|apply|verify
        self.calls: list[str] = []

    def precondition(self, ctx):
        self.calls.append("precondition")
        if self.fail_at == "precondition":
            return False, "nema uslova"
        return True, "uslov ok"

    def snapshot(self, ctx):
        self.calls.append("snapshot")
        if self.fail_at == "snapshot":
            raise RuntimeError("snapshot kvar")
        return {"marker": 1}

    def apply(self, ctx, state):
        self.calls.append("apply")
        if self.fail_at == "apply":
            raise RuntimeError("apply kvar")

    def verify(self, ctx, state):
        self.calls.append("verify")
        if self.fail_at == "verify":
            return False, "nije popravljeno"
        return True, "popravljeno"

    def rollback(self, ctx, state):
        self.calls.append("rollback")
        assert state["marker"] == 1


def run_fake(fail_at, **ctx_kw):
    with tempfile.TemporaryDirectory() as tmp:
        ctx = ActionContext(quarantine_dir=tmp, **ctx_kw)
        runner = Runner()
        action = FakeAction(fail_at)
        return runner.run(action, ctx), action, runner


class TestRunnerContract(unittest.TestCase):
    def test_happy_path_no_rollback(self):
        result, action, runner = run_fake(None)
        self.assertTrue(result.ok and result.verified)
        self.assertFalse(result.rolled_back)
        self.assertEqual(action.calls,
                         ["precondition", "snapshot", "apply", "verify"])

    def test_verify_fail_triggers_rollback(self):
        result, action, _ = run_fake("verify")
        self.assertFalse(result.ok)
        self.assertTrue(result.rolled_back)
        self.assertEqual(action.calls[-1], "rollback")
        self.assertIn("vraceno", result.message)

    def test_apply_fail_triggers_rollback(self):
        result, action, _ = run_fake("apply")
        self.assertFalse(result.ok and result.verified)
        self.assertTrue(result.rolled_back)

    def test_precondition_fail_runs_nothing(self):
        result, action, _ = run_fake("precondition")
        self.assertFalse(result.ok)
        self.assertEqual(action.calls, ["precondition"])

    def test_snapshot_fail_runs_no_apply(self):
        result, action, _ = run_fake("snapshot")
        self.assertFalse(result.ok)
        self.assertNotIn("apply", action.calls)
        self.assertFalse(result.rolled_back)  # nema sta vratiti

    def test_dry_run_changes_nothing(self):
        result, action, _ = run_fake(None, dry_run=True)
        self.assertEqual(action.calls, ["precondition"])
        self.assertIn("nista nije mijenjano", result.message)

    def test_cancelled_runs_nothing(self):
        result, action, _ = run_fake(None, dry_run=False)
        with tempfile.TemporaryDirectory() as tmp:
            ctx = ActionContext(quarantine_dir=tmp)
            ctx.cancelled = True
            result = Runner().run(FakeAction(None), ctx)
        self.assertFalse(result.ok)
        self.assertIn("otkazano", result.message)

    def test_audit_log_covers_run(self):
        _, _, runner = run_fake("verify")
        phases = [e["phase"] for e in runner.audit]
        self.assertIn("verify", phases)
        self.assertIn("rollback", phases)
        self.assertTrue(all("action" in e and "ok" in e for e in runner.audit))


class TestQuarantine(unittest.TestCase):
    def test_move_and_restore_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            victim = os.path.join(tmp, "f.txt")
            with open(victim, "w") as handle:
                handle.write("podaci")
            qdir = os.path.join(tmp, "q")
            record = quarantine_file(victim, qdir)
            self.assertFalse(os.path.exists(victim))
            restore_quarantined(record)
            with open(victim) as handle:
                self.assertEqual(handle.read(), "podaci")

    def test_restore_idempotent(self):
        record = {"original": "/ne/postoji/x", "quarantined": "/ne/postoji/y"}
        restore_quarantined(record)  # ne smije baciti


class TestCatalog(unittest.TestCase):
    def test_register_decorator(self):
        @__import__("mujofix.actions.base", fromlist=["register"]).register
        class Probe(Action):
            name = "probe-x"

            def precondition(self, ctx):
                return True, ""

            def snapshot(self, ctx):
                return {}

            def apply(self, ctx, state):
                pass

            def verify(self, ctx, state):
                return True, ""

            def rollback(self, ctx, state):
                pass

        self.assertIs(CATALOG["probe-x"], Probe)
        del CATALOG["probe-x"]


if __name__ == "__main__":
    unittest.main()

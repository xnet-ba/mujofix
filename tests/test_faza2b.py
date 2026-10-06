"""Testovi Faze 2b: apply -> verify -> rollback -> identicno stanje, za sve 3.

Registry i `sc` su mockovani (dict-fasada + fake proces); pravi Windows API
ce se vrtjeti na VM-u u rucnoj test-listi (docs/TESTING.md, Faza 6).
"""

import os
import sys
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mujofix.actions import service as service_mod
from mujofix.actions import startup as startup_mod
from mujofix.actions.base import ActionContext, CATALOG, Runner
from mujofix.actions.service import RestartService
from mujofix.actions.startup import DisableStartupItem
from mujofix.actions.temp import CleanTemp


class FakeRegistry:
    """Dict kao registry: {(hive, path): {name: value}}."""

    def __init__(self):
        self.data: dict[tuple[str, str], dict[str, str]] = {}

    def read(self, hive, path, name):
        return self.data.get((hive, path), {}).get(name)

    def delete(self, hive, path, name):
        del self.data[(hive, path)][name]

    def set(self, hive, path, name, value):
        self.data.setdefault((hive, path), {})[name] = value


def patch_registry(fake: FakeRegistry):
    return (
        patch.object(startup_mod, "_read_value", side_effect=fake.read),
        patch.object(startup_mod, "_delete_value", side_effect=fake.delete),
        patch.object(startup_mod, "_set_value", side_effect=fake.set),
        patch("mujofix.platform.windows.is_windows", return_value=True),
    )


class TestDisableStartupItem(unittest.TestCase):
    def test_roundtrip_identical(self):
        fake = FakeRegistry()
        hive, path = "HKCU", r"Software\X\Run"
        fake.set(hive, path, "Foo", "C:\\foo.exe")
        patches = patch_registry(fake)
        with patches[0], patches[1], patches[2], patches[3]:
            with tempfile.TemporaryDirectory() as tmp:
                runner = Runner()
                action = DisableStartupItem(hive, path, "Foo")
                result = runner.run(action, ActionContext(quarantine_dir=tmp))
                self.assertTrue(result.ok and result.verified, result.message)
                self.assertIsNone(fake.read(hive, path, "Foo"))
                # rollback rucno: stanje identicno originalu
                action.rollback(ActionContext(quarantine_dir=tmp),
                                {"hive": hive, "path": path,
                                 "entry": "Foo", "value": "C:\\foo.exe"})
                self.assertEqual(fake.read(hive, path, "Foo"), "C:\\foo.exe")

    def test_runner_rolls_back_on_verify_fail(self):
        fake = FakeRegistry()
        fake.set("HKCU", "P", "Foo", "C:\\foo.exe")
        patches = patch_registry(fake)
        with patches[0], patches[1], patches[2], patches[3]:
            with tempfile.TemporaryDirectory() as tmp:
                action = DisableStartupItem("HKCU", "P", "Foo")
                # apply ne brise nista -> verify pada -> rollback vraca vrijednost
                with patch.object(startup_mod, "_delete_value",
                                  side_effect=lambda h, p, n: None):
                    result = Runner().run(action,
                                          ActionContext(quarantine_dir=tmp))
                self.assertFalse(result.ok)
                self.assertTrue(result.rolled_back)
                self.assertEqual(fake.read("HKCU", "P", "Foo"), "C:\\foo.exe")

    def test_missing_entry_precondition_fails(self):
        fake = FakeRegistry()
        patches = patch_registry(fake)
        with patches[0], patches[1], patches[2], patches[3]:
            with tempfile.TemporaryDirectory() as tmp:
                result = Runner().run(
                    DisableStartupItem("HKCU", "P", "Nope"),
                    ActionContext(quarantine_dir=tmp))
                self.assertFalse(result.ok)
                self.assertIn("ne postoji", result.message)


class TestCleanTemp(unittest.TestCase):
    def test_roundtrip_identical(self):
        # faze direktno (Runner ožičenje dokazano u test_faza2a + startup testu)
        with tempfile.TemporaryDirectory() as tmp:
            victim = os.path.join(tmp, "old.tmp")
            with open(victim, "w") as handle:
                handle.write("podaci")
            old = time.time() - 30 * 86400
            os.utime(victim, (old, old))
            qdir = os.path.join(tmp, "q")
            ctx = ActionContext(quarantine_dir=qdir)
            action = CleanTemp(tmp, older_than_days=7)
            ok, _ = action.precondition(ctx)
            self.assertTrue(ok)
            state = action.snapshot(ctx)
            action.apply(ctx, state)
            verified, _ = action.verify(ctx, state)
            self.assertTrue(verified)
            self.assertFalse(os.path.exists(victim))
            action.rollback(ctx, state)
            with open(victim) as handle:
                self.assertEqual(handle.read(), "podaci")

    def test_fresh_files_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            fresh = os.path.join(tmp, "new.tmp")
            with open(fresh, "w") as handle:
                handle.write("svjeze")
            qdir = os.path.join(tmp, "q")
            result = Runner().run(CleanTemp(tmp, older_than_days=7),
                                  ActionContext(quarantine_dir=qdir))
            self.assertFalse(result.ok)  # nema kandidata
            self.assertTrue(os.path.exists(fresh))


class TestCleanTempManifest(unittest.TestCase):
    def test_manifest_written(self):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            victim = os.path.join(tmp, "old.tmp")
            with open(victim, "w") as handle:
                handle.write("x")
            old = time.time() - 30 * 86400
            os.utime(victim, (old, old))
            qdir = os.path.join(tmp, "q")
            result = Runner().run(CleanTemp(tmp, older_than_days=7),
                                  ActionContext(quarantine_dir=qdir))
            self.assertTrue(result.ok)
            with open(os.path.join(qdir, "clean_temp-manifest.json")) as handle:
                records = json.load(handle)
            self.assertEqual(len(records), 1)
            self.assertTrue(records[0]["quarantined"].startswith(qdir))


class FakeSC:
    """Fake `sc`: stanja servisa u dictu."""

    def __init__(self, states: dict[str, str]):
        self.states = dict(states)
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, *args: str):
        self.calls.append(args)
        proc = MagicMock()
        verb, service = args[0], args[1]
        if verb == "query":
            if service not in self.states:
                proc.returncode = 1060
                proc.stdout, proc.stderr = "", "service does not exist"
            else:
                code = {"RUNNING": 4, "STOPPED": 1}.get(self.states[service], 1)
                proc.returncode = 0
                proc.stdout = (f"SERVICE_NAME: {service}\n"
                               f"        STATE              : {code}  "
                               f"{self.states[service]}\n")
                proc.stderr = ""
        elif verb == "stop":
            self.states[service] = "STOPPED"
            proc.returncode, proc.stdout, proc.stderr = 0, "", ""
        elif verb == "start":
            self.states[service] = "RUNNING"
            proc.returncode, proc.stdout, proc.stderr = 0, "", ""
        return proc


class TestRestartService(unittest.TestCase):
    def test_roundtrip_stopped_service_runs(self):
        fake = FakeSC({"Spooler": "STOPPED"})
        with patch("mujofix.platform.windows.is_windows", return_value=True), \
             patch.object(service_mod, "_sc", side_effect=fake):
            with tempfile.TemporaryDirectory() as tmp:
                result = Runner().run(RestartService("Spooler"),
                                      ActionContext(quarantine_dir=tmp))
                self.assertTrue(result.ok and result.verified, result.message)
                self.assertEqual(fake.states["Spooler"], "RUNNING")
                self.assertIn(("stop", "Spooler"), fake.calls)
                self.assertIn(("start", "Spooler"), fake.calls)

    def test_missing_service_precondition_fails(self):
        fake = FakeSC({})
        with patch("mujofix.platform.windows.is_windows", return_value=True), \
             patch.object(service_mod, "_sc", side_effect=fake):
            with tempfile.TemporaryDirectory() as tmp:
                result = Runner().run(RestartService("Nope"),
                                      ActionContext(quarantine_dir=tmp))
                self.assertFalse(result.ok)
                self.assertIn("ne postoji", result.message)

    def test_catalog_has_all_three(self):
        self.assertEqual(
            {k for k in CATALOG if k in ("disable_startup_item", "clean_temp",
                                        "restart_service")},
            {"disable_startup_item", "clean_temp", "restart_service"})


if __name__ == "__main__":
    unittest.main()

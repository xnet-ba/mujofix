"""Testovi Faza 2c: akcije bez UAC-a (PATH unos, TEMP/TMP, proxy).

Isti ugovor kao Faza 2b: apply -> verify -> rollback -> identicno stanje, uz
dict-fasadu registryja. Pravi winreg ide na VM-u (docs/TESTING.md).
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mujofix.actions import env as env_mod
from mujofix.actions.base import CATALOG, ActionContext, Runner
from mujofix.actions.duplicates import QuarantineDuplicates
from mujofix.actions.env import FixTempVar, RemovePathEntry
from mujofix.actions.proxy import INTERNET_SETTINGS, DisableProxy

REG_SZ = 1
REG_DWORD = 4


class FakeEnvRegistry:
    """Dict kao registry: {(hive, key, name): (vrijednost, tip)}."""

    def __init__(self):
        self.data: dict[tuple[str, str, str], tuple] = {}

    def read(self, hive, key, name):
        return self.data.get((hive, key, name), (None, REG_SZ))

    def write(self, hive, key, name, value, kind):
        self.data[(hive, key, name)] = (value, kind)

    def set(self, hive, key, name, value, kind=REG_SZ):
        self.data[(hive, key, name)] = (value, kind)


def patch_env(fake: FakeEnvRegistry):
    return (
        patch.object(env_mod, "read_env", side_effect=fake.read),
        patch.object(env_mod, "write_env", side_effect=fake.write),
        patch("mujofix.platform.windows.is_windows", return_value=True),
    )


def _run(action, tmp):
    return Runner().run(action, ActionContext(quarantine_dir=tmp))


class TestRemovePathEntry(unittest.TestCase):
    def test_roundtrip_identical(self):
        fake = FakeEnvRegistry()
        original = r"C:\Windows;C:\Ghost;C:\Tools"
        fake.set("HKCU", env_mod.USER_ENV, "Path", original)
        p = patch_env(fake)
        with p[0], p[1], p[2]:
            with tempfile.TemporaryDirectory() as tmp:
                action = RemovePathEntry(r"C:\Ghost")
                result = _run(action, tmp)
                self.assertTrue(result.ok and result.verified, result.message)
                self.assertEqual(fake.read("HKCU", env_mod.USER_ENV, "Path")[0],
                                 r"C:\Windows;C:\Tools")
                action.rollback(ActionContext(quarantine_dir=tmp), result.state)
                self.assertEqual(fake.read("HKCU", env_mod.USER_ENV, "Path")[0],
                                 original)

    def test_hklm_entry_needs_elevation(self):
        fake = FakeEnvRegistry()
        fake.set("HKLM", env_mod.SYSTEM_ENV, "Path", r"C:\Windows;C:\Dead")
        p = patch_env(fake)
        with p[0], p[1], p[2]:
            self.assertTrue(RemovePathEntry(r"C:\Dead").needs_elevation)

    def test_missing_entry_precondition_fails(self):
        fake = FakeEnvRegistry()
        fake.set("HKCU", env_mod.USER_ENV, "Path", r"C:\Windows")
        p = patch_env(fake)
        with p[0], p[1], p[2]:
            with tempfile.TemporaryDirectory() as tmp:
                result = _run(RemovePathEntry(r"C:\Nope"), tmp)
                self.assertFalse(result.ok)
                self.assertIn("nije u PATH-u", result.message)


class TestFixTempVar(unittest.TestCase):
    def test_roundtrip_identical(self):
        fake = FakeEnvRegistry()
        fake.set("HKCU", env_mod.USER_ENV, "TEMP", r"C:\Nope\Temp")
        with tempfile.TemporaryDirectory() as real:
            p = patch_env(fake)
            with p[0], p[1], p[2]:
                with tempfile.TemporaryDirectory() as tmp:
                    action = FixTempVar("TEMP", target=real)
                    result = _run(action, tmp)
                    self.assertTrue(result.ok and result.verified, result.message)
                    self.assertEqual(
                        fake.read("HKCU", env_mod.USER_ENV, "TEMP")[0], real)
                    action.rollback(ActionContext(quarantine_dir=tmp),
                                    result.state)
                    self.assertEqual(
                        fake.read("HKCU", env_mod.USER_ENV, "TEMP")[0],
                        r"C:\Nope\Temp")

    def test_valid_temp_untouched(self):
        fake = FakeEnvRegistry()
        with tempfile.TemporaryDirectory() as good:
            fake.set("HKCU", env_mod.USER_ENV, "TMP", good)
            p = patch_env(fake)
            with p[0], p[1], p[2]:
                with tempfile.TemporaryDirectory() as tmp:
                    result = _run(FixTempVar("TMP", target=good), tmp)
                    self.assertFalse(result.ok)
                    self.assertIn("vec ispravan", result.message)


class TestDisableProxy(unittest.TestCase):
    def test_roundtrip_identical(self):
        fake = FakeEnvRegistry()
        fake.set("HKCU", INTERNET_SETTINGS, "ProxyEnable", 1, REG_DWORD)
        p = patch_env(fake)
        with p[0], p[1], p[2]:
            with tempfile.TemporaryDirectory() as tmp:
                result = _run(DisableProxy(), tmp)
                self.assertTrue(result.ok and result.verified, result.message)
                self.assertEqual(
                    fake.read("HKCU", INTERNET_SETTINGS, "ProxyEnable")[0], 0)
                DisableProxy().rollback(ActionContext(quarantine_dir=tmp),
                                        result.state)
                self.assertEqual(
                    fake.read("HKCU", INTERNET_SETTINGS, "ProxyEnable")[0], 1)

    def test_not_enabled_precondition_fails(self):
        fake = FakeEnvRegistry()
        fake.set("HKCU", INTERNET_SETTINGS, "ProxyEnable", 0, REG_DWORD)
        p = patch_env(fake)
        with p[0], p[1], p[2]:
            with tempfile.TemporaryDirectory() as tmp:
                result = _run(DisableProxy(), tmp)
                self.assertFalse(result.ok)
                self.assertIn("nije ukljucen", result.message)


class TestQuarantineDuplicates(unittest.TestCase):
    @staticmethod
    def _mk(tmp, name, data=b"isti podaci"):
        path = os.path.join(tmp, name)
        with open(path, "wb") as handle:
            handle.write(data)
        return path

    def test_roundtrip_keeps_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            qdir = os.path.join(tmp, "q")
            first = self._mk(tmp, "a.bin")
            second = self._mk(tmp, "b.bin")
            action = QuarantineDuplicates(
                [{"certain": True, "size": 11, "paths": [first, second]}])
            result = _run(action, qdir)
            self.assertTrue(result.ok and result.verified, result.message)
            self.assertTrue(os.path.exists(first))
            self.assertFalse(os.path.exists(second))
            action.rollback(ActionContext(quarantine_dir=qdir), result.state)
            self.assertTrue(os.path.exists(second))

    def test_uncertain_group_is_recommendation_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = self._mk(tmp, "a.bin")
            second = self._mk(tmp, "b.bin")
            action = QuarantineDuplicates(
                [{"certain": False, "paths": [first, second]}])
            result = _run(action, tmp)
            self.assertFalse(result.ok)
            self.assertIn("potvrdjenih", result.message)
            self.assertTrue(os.path.exists(second))


class TestElevation(unittest.TestCase):
    def test_is_admin_false_off_windows(self):
        from mujofix.platform import windows
        if windows.is_windows():
            self.skipTest("samo ne-Windows grana")
        self.assertFalse(windows.is_admin())

    def test_relaunch_elevated_unsupported_off_windows(self):
        from mujofix.platform import windows
        if windows.is_windows():
            self.skipTest("samo ne-Windows grana")
        with self.assertRaises(windows.NotSupported):
            windows.relaunch_elevated()


class TestWiring(unittest.TestCase):
    def test_new_actions_registered(self):
        for name in ("remove_path_entry", "fix_temp_var", "disable_proxy",
                     "quarantine_duplicates"):
            self.assertIn(name, CATALOG)

    def test_findings_map_to_actions(self):
        from mujofix.actions.mapping import finding_to_actions
        names = lambda fid, ev: [a.name for a in
                                 finding_to_actions({"id": fid, "evidence": ev})]
        self.assertEqual(names("config-path-missing", {"entries": [r"C:\X"]}),
                         ["remove_path_entry"])
        self.assertEqual(names("config-temp-var", {"var": "TEMP"}), ["fix_temp_var"])
        self.assertEqual(
            names("network-proxy", {"proxy": {"registry": "h:8080"}}),
            ["disable_proxy"])
        self.assertEqual(names("network-proxy", {"proxy": {"HTTP_PROXY": "x"}}), [])
        self.assertEqual(
            names("duplicates-found",
                  {"groups": [{"certain": True, "paths": ["a", "b"]}]}),
            ["quarantine_duplicates"])
        self.assertEqual(
            names("duplicates-found",
                  {"groups": [{"certain": False, "paths": ["a", "b"]}]}),
            [])


if __name__ == "__main__":
    unittest.main()

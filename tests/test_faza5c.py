"""Testovi Faze 5c: sumnjivi procesi i permisije (mock PS/registry/subprocesa)."""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import mujofix.scanners.suspicious as susp_mod
from mujofix.scanners.base import ScanContext
from mujofix.scanners.permissions import PermissionsScanner
from mujofix.scanners.suspicious import SuspiciousScanner


def ps_result(payload: object, returncode: int = 0):
    proc = MagicMock(returncode=returncode,
                     stdout=json.dumps(payload), stderr="")
    return proc


class TestSuspiciousScanner(unittest.TestCase):
    def processes(self):
        return [
            {"Name": "evil", "Id": 123,
             "Path": "C:\\Users\\A\\AppData\\Local\\Temp\\evil.exe"},
            {"Name": "good", "Id": 124, "Path": "C:\\Windows\\good.exe"},
            {"Name": "sys", "Id": 4, "Path": None},
        ]

    def run_scan(self, processes, sig_status="Unknown", defender=True):
        def fake_run(cmd, **kw):
            text = cmd[-1]
            if "Get-Process" in text:
                return ps_result(processes)
            if "Get-AuthenticodeSignature" in text:
                return ps_result(sig_status)
            if "RealTimeProtectionEnabled" in text:
                return ps_result(defender)
            raise AssertionError(f"neocekivan poziv: {text[:60]}")

        with patch("mujofix.platform.windows.is_windows", return_value=True), \
             patch("subprocess.run", side_effect=fake_run), \
             patch.dict(os.environ, {"TEMP": "C:\\Users\\A\\AppData\\Local\\Temp",
                                     "TMP": "C:\\Users\\A\\AppData\\Local\\Temp",
                                     "SystemRoot": "C:\\Windows",
                                     "LOCALAPPDATA": "C:\\Users\\A\\AppData\\Local"}), \
             patch("mujofix.platform.windows.read_reg_values", return_value={}), \
             patch("mujofix.platform.windows.startup_folders", return_value=[]):
            return SuspiciousScanner().scan(ScanContext())

    def test_temp_process_flagged_not_virus(self):
        report = self.run_scan(self.processes())
        by_id = {f.id: f for f in report.findings}
        finding = by_id["suspicious-process"]
        self.assertIn("ne tvrdimo da je virus", finding.title)
        self.assertIn("evil", str(finding.evidence))
        self.assertNotIn("good", str(finding.evidence["suspects"]))
        self.assertFalse(finding.reversible)

    def test_defender_off_flagged(self):
        report = self.run_scan(self.processes(), defender=False)
        by_id = {f.id: f for f in report.findings}
        self.assertEqual(by_id["suspicious-defender-off"].severity, "MEDIUM")

    def test_clean_system_no_findings(self):
        report = self.run_scan(
            [{"Name": "good", "Id": 1, "Path": "C:\\Windows\\good.exe"}],
            sig_status="Valid", defender=True)
        self.assertEqual(report.findings, [])


class TestPermissionsScanner(unittest.TestCase):
    def test_uac_off_is_critical(self):
        with patch("mujofix.platform.windows.is_windows", return_value=True), \
             patch("mujofix.platform.windows.read_reg_values",
                   return_value={"EnableLUA": "0 "}), \
             patch("os.path.isdir", return_value=False), \
             patch("subprocess.run",
                   side_effect=lambda *a, **k: MagicMock(returncode=1,
                                                         stdout="", stderr="")):
            report = PermissionsScanner().scan(ScanContext())
        by_id = {f.id: f for f in report.findings}
        self.assertEqual(by_id["permissions-uac-off"].severity, "CRITICAL")
        self.assertTrue(by_id["permissions-uac-off"].reversible)

    def test_uac_on_no_finding(self):
        with patch("mujofix.platform.windows.is_windows", return_value=True), \
             patch("mujofix.platform.windows.read_reg_values",
                   return_value={"EnableLUA": "1"}), \
             patch("os.path.isdir", return_value=False), \
             patch("subprocess.run",
                   side_effect=lambda *a, **k: MagicMock(returncode=1,
                                                         stdout="", stderr="")):
            report = PermissionsScanner().scan(ScanContext())
        self.assertEqual(report.findings, [])

    def test_weak_acl_flagged(self):
        icacls = ("C:\\Windows BUILTIN\\Users:(OI)(CI)(W)\n"
                  "  NT AUTHORITY\\SYSTEM:(OI)(CI)(F)")
        def fake_run(cmd, **kw):
            if cmd[0] == "icacls":
                return MagicMock(returncode=0, stdout=icacls, stderr="")
            return MagicMock(returncode=1, stdout="", stderr="")
        with patch("mujofix.platform.windows.is_windows", return_value=True), \
             patch("mujofix.platform.windows.read_reg_values",
                   return_value={"EnableLUA": "1"}), \
             patch("os.path.isdir", return_value=True), \
             patch("subprocess.run", side_effect=fake_run), \
             patch.dict(os.environ, {"SystemRoot": "C:\\Windows",
                                     "ProgramFiles": "C:\\Program Files"}):
            report = PermissionsScanner().scan(ScanContext())
        by_id = {f.id: f for f in report.findings}
        self.assertEqual(by_id["permissions-acl"].severity, "CRITICAL")

    def test_posix_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            wide = os.path.join(tmp, "wide")
            os.mkdir(wide)
            os.chmod(wide, 0o777)
            with patch("mujofix.platform.windows.is_windows",
                        return_value=False), \
                 patch.dict(os.environ, {"PATH": wide}):
                report = PermissionsScanner().scan(ScanContext())
        self.assertEqual(report.findings[0].id, "permissions-path-writable")


if __name__ == "__main__":
    unittest.main()

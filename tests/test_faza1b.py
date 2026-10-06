"""Testovi Faze 1b: disk, servisi, CLI (mock platforme/procesa)."""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mujofix import cli
from mujofix.scanners.base import REGISTRY, ScanContext
from mujofix.scanners.disk import DiskScanner, _dir_size
from mujofix.scanners.services import ServicesScanner


class TestDiskScanner(unittest.TestCase):
    def test_temp_finding_with_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "big.bin"), "wb") as handle:
                handle.write(b"\0" * 1024)
            with patch("tempfile.gettempdir", return_value=tmp), \
                 patch("mujofix.platform.windows.is_windows", return_value=False), \
                 patch("mujofix.scanners.disk.TEMP_BYTES_MEDIUM", 512):
                report = DiskScanner().scan(ScanContext())
        by_id = {f.id: f for f in report.findings}
        self.assertIn("disk-temp", by_id)
        self.assertEqual(by_id["disk-temp"].evidence["bytes"], 1024)
        self.assertTrue(by_id["disk-temp"].reversible)

    def test_dir_size_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "a"), "wb") as handle:
                handle.write(b"12345")
            size, count = _dir_size(tmp, ScanContext())
        self.assertEqual((size, count), (5, 1))

    def test_free_space_finding_shape(self):
        fake = MagicMock(total=100 * 1024**3, free=5 * 1024**3)
        with patch("shutil.disk_usage", return_value=fake), \
             patch("tempfile.gettempdir", return_value="/nonexistent-mujofix"), \
             patch("mujofix.platform.windows.is_windows", return_value=False):
            report = DiskScanner().scan(ScanContext())
        by_id = {f.id: f for f in report.findings}
        self.assertEqual(by_id["disk-almost-full"].severity, "CRITICAL")
        self.assertFalse(by_id["disk-almost-full"].reversible)


class TestServicesScanner(unittest.TestCase):
    def _fake_ps(self, payload):
        proc = MagicMock(returncode=0, stdout=json.dumps(payload), stderr="")
        return patch("subprocess.run", return_value=proc)

    def test_dead_auto_service_found(self):
        payload = [
            {"Name": "Spooler", "Status": "Stopped", "StartType": "Automatic"},
            {"Name": "W32Time", "Status": "Running", "StartType": "Automatic"},
            {"Name": "X", "Status": "Stopped", "StartType": "Manual"},
        ]
        with patch("mujofix.platform.windows.is_windows", return_value=True), \
                self._fake_ps(payload):
            report = ServicesScanner().scan(ScanContext())
        self.assertEqual(len(report.findings), 1)
        self.assertIn("Spooler", report.findings[0].evidence["sample"])
        self.assertNotIn("W32Time", report.findings[0].evidence["sample"])

    def test_all_healthy_no_findings(self):
        payload = [{"Name": "W32Time", "Status": "Running",
                    "StartType": "Automatic"}]
        with patch("mujofix.platform.windows.is_windows", return_value=True), \
                self._fake_ps(payload):
            report = ServicesScanner().scan(ScanContext())
        self.assertEqual(report.findings, [])

    def test_graceful_skip_off_windows(self):
        with patch("mujofix.platform.windows.is_windows", return_value=False):
            report = ServicesScanner().scan(ScanContext())
        self.assertIsNotNone(report.skipped)


class TestCli(unittest.TestCase):
    def test_scan_json_lists_all_scanners(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(cli.main(["scan"]), 0)
        reports = json.loads(buf.getvalue())
        self.assertEqual({r["scanner"] for r in reports}, set(REGISTRY))
        for report in reports:
            self.assertIn("findings", report)

    def test_summary_counts(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            cli.main(["scan", "--summary"])
        self.assertIn("problema", buf.getvalue())

    def test_unknown_scanner_reported(self):
        reports = cli.run_scan(["nepostojeci"])
        self.assertIn("nepoznat", reports[0]["skipped"])


if __name__ == "__main__":
    unittest.main()

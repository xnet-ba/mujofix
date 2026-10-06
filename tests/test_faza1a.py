"""Testovi Faze 1a: model, interfejs, startup scanner (mock Windows API-ja)."""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mujofix.core.models import Finding, ScanReport
from mujofix.scanners.base import REGISTRY, ScanContext, Scanner
from mujofix.scanners.startup import MEDIUM_THRESHOLD, StartupScanner


class TestFindingModel(unittest.TestCase):
    def test_evidence_required(self):
        with self.assertRaises(ValueError):
            Finding(id="x", scanner="s", title="t", why="w", severity="LOW",
                    impact="i", risk="r", reversible=True, evidence={})

    def test_bad_severity_rejected(self):
        with self.assertRaises(ValueError):
            Finding(id="x", scanner="s", title="t", why="w", severity="HIGH",
                    impact="i", risk="r", reversible=True, evidence={"a": 1})

    def test_to_dict_roundtrip(self):
        finding = Finding(id="x", scanner="s", title="t", why="w",
                          severity="MEDIUM", impact="i", risk="r",
                          reversible=False, evidence={"n": 2})
        self.assertEqual(finding.to_dict()["evidence"], {"n": 2})


class TestScannerContract(unittest.TestCase):
    def test_exception_becomes_skipped_not_crash(self):
        class Boom(Scanner):
            name = "boom"

            def _scan(self, ctx):
                raise RuntimeError("kvar")

        report = Boom().scan(ScanContext())
        self.assertIsNotNone(report.skipped)
        self.assertIn("RuntimeError", report.skipped)

    def test_registered(self):
        self.assertIs(REGISTRY["startup"], StartupScanner)


class TestStartupScanner(unittest.TestCase):
    def _run(self, reg: dict, folder_files: list[str]) -> ScanReport:
        calls = {"n": 0}

        def fake_reg(hive: str, path: str) -> dict:
            # isti sadrzaj samo za prvi Run kljuc, ostali prazni
            calls["n"] += 1
            return dict(reg) if calls["n"] == 1 else {}

        with tempfile.TemporaryDirectory() as tmp:
            for name in folder_files:
                open(os.path.join(tmp, name), "w").close()
            with patch("mujofix.platform.windows.is_windows", return_value=True), \
                 patch("mujofix.platform.windows.read_reg_values",
                       side_effect=fake_reg), \
                 patch("mujofix.platform.windows.startup_folders",
                       return_value=[tmp]):
                return StartupScanner().scan(ScanContext())

    def test_low_for_few_items(self):
        report = self._run({"One": "C:\\a.exe"}, ["x.lnk"])
        self.assertIsNone(report.skipped)
        self.assertEqual(len(report.findings), 1)
        finding = report.findings[0]
        self.assertEqual(finding.severity, "LOW")
        self.assertEqual(finding.evidence["count"], 2)
        self.assertTrue(finding.reversible)

    def test_medium_for_many_items(self):
        reg = {f"App{i}": f"C:\\a{i}.exe" for i in range(MEDIUM_THRESHOLD)}
        report = self._run(reg, [])
        self.assertEqual(report.findings[0].severity, "MEDIUM")

    def test_empty_startup_no_findings(self):
        report = self._run({}, [])
        self.assertIsNone(report.skipped)
        self.assertEqual(report.findings, [])

    def test_graceful_skip_off_windows(self):
        with patch("mujofix.platform.windows.is_windows", return_value=False):
            report = StartupScanner().scan(ScanContext())
        self.assertIsNotNone(report.skipped)
        self.assertEqual(report.findings, [])


if __name__ == "__main__":
    unittest.main()

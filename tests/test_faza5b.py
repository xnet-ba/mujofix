"""Testovi Faze 5b: drajveri (fake pnputil) i duplikati (pravi fajlovi)."""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import mujofix.scanners.duplicates as dup_mod
from mujofix.scanners.base import ScanContext
from mujofix.scanners.drivers import DriversScanner
from mujofix.scanners.duplicates import DuplicatesScanner

PNPUTIL_OUT = """
Published Name :     oem12.inf
Driver Package Provider : Intel
Class :              System
Driver Date and Version : 01/15/2015 1.0.0.1

Published Name :     oem13.inf
Driver Package Provider : NVIDIA
Class :              Display
Driver Date and Version : 06/01/2024 32.0.1.0

Published Name :     notaoem.inf
"""


class TestDriversScanner(unittest.TestCase):
    def fake_pnputil(self, stdout: str, returncode: int = 0):
        proc = MagicMock(returncode=returncode, stdout=stdout, stderr="")
        return patch("subprocess.run", return_value=proc)

    def test_old_driver_flagged(self):
        with patch("mujofix.platform.windows.is_windows", return_value=True), \
                self.fake_pnputil(PNPUTIL_OUT):
            report = DriversScanner().scan(ScanContext())
        self.assertIsNone(report.skipped)
        self.assertEqual(len(report.findings), 1)
        finding = report.findings[0]
        self.assertEqual(finding.id, "drivers-old")
        self.assertEqual(finding.evidence["count"], 1)
        self.assertEqual(finding.evidence["drivers"][0]["oem"], "oem12.inf")
        self.assertTrue(finding.reversible)

    def test_no_old_drivers_no_findings(self):
        out = PNPUTIL_OUT.replace("01/15/2015", "06/01/2024")
        with patch("mujofix.platform.windows.is_windows", return_value=True), \
                self.fake_pnputil(out):
            report = DriversScanner().scan(ScanContext())
        self.assertEqual(report.findings, [])

    def test_garbage_output_becomes_skipped(self):
        with patch("mujofix.platform.windows.is_windows", return_value=True), \
                self.fake_pnputil("nista prepoznatljivo"):
            report = DriversScanner().scan(ScanContext())
        self.assertIsNotNone(report.skipped)
        self.assertIn("neprepoznat", report.skipped)

    def test_graceful_skip_off_windows(self):
        with patch("mujofix.platform.windows.is_windows", return_value=False):
            report = DriversScanner().scan(ScanContext())
        self.assertIsNotNone(report.skipped)


class TestDuplicatesScanner(unittest.TestCase):
    def write(self, directory: str, name: str, content: bytes) -> str:
        path = os.path.join(directory, name)
        with open(path, "wb") as handle:
            handle.write(content)
        return path

    def test_certain_duplicates_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            blob = b"A" * 1024
            self.write(tmp, "a.bin", blob)
            self.write(tmp, "b.bin", blob)
            self.write(tmp, "c.bin", b"B" * 1024)  # ista velicina, drugaciji
            with patch.object(dup_mod, "MIN_SIZE_BYTES", 512):
                report = DuplicatesScanner(roots=[tmp]).scan(ScanContext())
        self.assertEqual(len(report.findings), 1)
        finding = report.findings[0]
        self.assertTrue(finding.evidence["groups"][0]["certain"])
        self.assertEqual(
            sorted(os.path.basename(p)
                   for p in finding.evidence["groups"][0]["paths"]),
            ["a.bin", "b.bin"])
        self.assertFalse(finding.reversible)  # nikad auto-brisanje

    def test_small_files_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, "a.bin", b"A" * 100)
            self.write(tmp, "b.bin", b"A" * 100)
            with patch.object(dup_mod, "MIN_SIZE_BYTES", 512):
                report = DuplicatesScanner(roots=[tmp]).scan(ScanContext())
        self.assertEqual(report.findings, [])

    def test_big_files_probable_not_certain(self):
        with tempfile.TemporaryDirectory() as tmp:
            blob = b"Z" * 2048
            self.write(tmp, "a.bin", blob)
            self.write(tmp, "b.bin", blob)
            with patch.object(dup_mod, "MIN_SIZE_BYTES", 512), \
                 patch.object(dup_mod, "FULL_HASH_CAP_BYTES", 1024):
                report = DuplicatesScanner(roots=[tmp]).scan(ScanContext())
        group = report.findings[0].evidence["groups"][0]
        self.assertFalse(group["certain"])
        self.assertIn("note", group)  # nesigurnost izricito navedena

    def test_excluded_dirs_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            sub = os.path.join(tmp, ".git")
            os.mkdir(sub)
            blob = b"Q" * 1024
            self.write(sub, "a.bin", blob)
            self.write(sub, "b.bin", blob)
            with patch.object(dup_mod, "MIN_SIZE_BYTES", 512):
                report = DuplicatesScanner(roots=[tmp]).scan(ScanContext())
        self.assertEqual(report.findings, [])


if __name__ == "__main__":
    unittest.main()

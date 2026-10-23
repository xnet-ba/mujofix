"""Defender izuzeci: prijavljujemo, NE mijenjamo (politika app-a)."""

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import mujofix.scanners.suspicious as sus
from mujofix.actions.mapping import finding_to_actions
from mujofix.scanners.base import ScanContext

BS_CHARS = "čćžšđ"


def fake_ps(preference: object, realtime: object = True):
    """`_ps_json` koji odgovara razlicito na MpComputerStatus i MpPreference."""
    def _call(command: str, **kwargs):
        if "MpComputerStatus" in command:
            return realtime
        if "MpPreference" in command:
            return preference
        raise AssertionError(f"neocekivan PS poziv: {command[:60]}")
    return _call


class TestDefenderExclusions(unittest.TestCase):
    def _scan(self, preference, lang="bs"):
        with patch.object(sus, "_ps_json", fake_ps(preference)), \
             patch.object(sus, "_processes", return_value=[]), \
             patch.object(sus.windows, "is_windows", return_value=True), \
             patch("mujofix.platform.windows.read_reg_values",
                   return_value={}), \
             patch("mujofix.platform.windows.startup_folders",
                   return_value=[]):
            report = sus.SuspiciousScanner().scan(ScanContext(lang=lang))
        self.assertFalse(report.skipped, report.skipped)
        return report

    def test_broad_exclusion_is_medium(self):
        report = self._scan({"Path": [r"C:\Temp\\"], "Process": [],
                             "Extension": [".ps1"]})
        ids = [f.id for f in report.findings]
        self.assertIn("defender-exclusions", ids)
        finding = [f for f in report.findings
                   if f.id == "defender-exclusions"][0]
        self.assertEqual(finding.severity, "MEDIUM")
        self.assertEqual(finding.evidence["count"], 2)
        self.assertEqual(finding.evidence["broad"], [r"C:\Temp\\"])

    def test_narrow_exclusion_is_low(self):
        report = self._scan({"Path": [r"C:\Program Files\App\\"],
                             "Process": [], "Extension": []})
        finding = [f for f in report.findings
                   if f.id == "defender-exclusions"][0]
        self.assertEqual(finding.severity, "LOW")
        self.assertEqual(finding.evidence["broad"], [])

    def test_no_exclusions_no_finding(self):
        report = self._scan({"Path": [], "Process": [], "Extension": []})
        self.assertEqual([f.id for f in report.findings], [])

    def test_has_no_fix_by_policy(self):
        """Mijenjanje Defender politika je izvan politike app-a."""
        self.assertEqual(finding_to_actions(
            {"id": "defender-exclusions", "scanner": "suspicious",
             "evidence": {"path": ["C:\\Temp\\"]}}), [])

    def test_powershell_shapes_and_failure_do_not_crash(self):
        # jedan izuzetak kao string (PowerShell vrati string, ne listu)
        report = self._scan({"Path": r"C:\Users\x\data", "Process": None,
                             "Extension": None})
        finding = [f for f in report.findings
                   if f.id == "defender-exclusions"][0]
        self.assertEqual(finding.evidence["count"], 1)
        self.assertEqual(finding.severity, "MEDIUM")  # \users\ je siroko

        def boom(command, **kwargs):
            raise RuntimeError("nema Defendera")

        with patch.object(sus, "_ps_json", boom), \
             patch.object(sus, "_processes", return_value=[]), \
             patch.object(sus.windows, "is_windows", return_value=True), \
             patch("mujofix.platform.windows.read_reg_values",
                   return_value={}), \
             patch("mujofix.platform.windows.startup_folders",
                   return_value=[]):
            report = sus.SuspiciousScanner().scan(ScanContext(lang="en"))
        self.assertNotIn("defender-exclusions", [f.id for f in report.findings])

    def test_messages_bilingual_and_english_clean(self):
        bs = self._scan({"Path": [r"C:\Temp\\"], "Process": [], "Extension": []},
                        "bs").findings[0]
        en = self._scan({"Path": [r"C:\Temp\\"], "Process": [], "Extension": []},
                        "en").findings[0]
        self.assertIn("izuzetaka", bs.title)
        self.assertIn("exclusions", en.title)
        for text in (en.title, en.why, en.impact, en.risk):
            self.assertFalse(set(BS_CHARS) & set(text.lower()), text)
        self.assertIn("WE NEVER CHANGE THEM", en.why)  # politika je u tekstu

    def test_is_broad_heuristics(self):
        for entry in ("C:\\", "*", r"C:\Users\x", r"C:\Users\x\AppData\Local",
                      r"C:\Windows\Temp\x.exe", r"C:\x\Downloads\y"):
            self.assertTrue(sus._is_broad(entry), entry)
        for entry in (r"C:\Program Files\App", r"D:\Games\Setup.exe",
                      r"C:\tools\dev"):
            self.assertFalse(sus._is_broad(entry), entry)


if __name__ == "__main__":
    unittest.main()

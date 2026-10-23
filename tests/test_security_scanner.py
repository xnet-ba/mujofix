"""Security scanner: BitLocker/Secure Boot/TPM/WU servis (fake PowerShell)."""

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import mujofix.scanners.security as sec
from mujofix.actions.mapping import finding_to_actions
from mujofix.scanners.base import ScanContext

BS_CHARS = "čćžšđ"


def fake_ps(answers: dict, failing: tuple = ()):
    """`ps_json` koji odgovara po sadrzaju komande; `failing` -> dize."""
    def _call(command: str, timeout_s: int = 60):
        if any(key in command for key in failing):
            raise RuntimeError("PowerShell greska")
        for key, value in answers.items():
            if key in command:
                return value
        raise AssertionError(f"neocekivan PS poziv: {command[:60]}")
    return _call


ALL_GOOD = {
    "Get-BitLockerVolume": {"Status": "On", "Volume": "FullyEncrypted"},
    "Confirm-SecureBootUEFI": "True",
    "Get-Tpm": {"Present": True, "Ready": True},
    "Get-Service": {"StartType": "Automatic"},
}


class TestSecurityScanner(unittest.TestCase):
    def _scan(self, answers, lang="bs", failing=(), expect_findings=True):
        with patch.object(sec, "_ps", fake_ps(answers, failing)), \
             patch.object(sec.windows, "is_windows", return_value=True):
            report = sec.SecurityScanner().scan(ScanContext(lang=lang))
        if expect_findings:
            self.assertFalse(report.skipped, report.skipped)
        return report

    def test_healthy_machine_reports_nothing(self):
        self.assertEqual(self._scan(ALL_GOOD).findings, [])

    def test_each_problem_is_reported_with_its_severity(self):
        report = self._scan({
            "Get-BitLockerVolume": {"Status": "Off", "Volume": "FullyDecrypted"},
            "Confirm-SecureBootUEFI": "False",
            "Get-Tpm": {"Present": False, "Ready": False},
            "Get-Service": {"StartType": "Disabled"},
        })
        by_id = {f.id: f for f in report.findings}
        self.assertEqual(set(by_id), {"bitlocker-off", "secureboot-off",
                                      "tpm-absent", "wuauserv-disabled"})
        self.assertEqual(by_id["bitlocker-off"].severity, "MEDIUM")
        self.assertEqual(by_id["secureboot-off"].severity, "MEDIUM")
        self.assertEqual(by_id["tpm-absent"].severity, "LOW")
        self.assertEqual(by_id["wuauserv-disabled"].severity, "MEDIUM")
        self.assertIn("(off)", by_id["bitlocker-off"].title)

    def test_disabled_wu_is_medium_manual_is_low(self):
        manual = self._scan({**ALL_GOOD, "Get-Service": {"StartType": "Manual"}})
        self.assertEqual(manual.findings[0].id, "wuauserv-disabled")
        self.assertEqual(manual.findings[0].severity, "LOW")

    def test_one_failing_check_does_not_hide_the_others(self):
        """BitLocker se ne moze procitati -> ostale provjere se i dalje rade."""
        report = self._scan({**ALL_GOOD, "Confirm-SecureBootUEFI": "False"},
                            failing=("Get-BitLockerVolume",))
        self.assertEqual([f.id for f in report.findings], ["secureboot-off"])

    def test_nothing_checkable_is_skipped_not_reported_healthy(self):
        """Ako nijedna provjera nije izvediva -> skipped, nikad 'sve je u redu'."""
        with patch.object(sec, "_ps", fake_ps({}, failing=(
                "Get-BitLockerVolume", "Confirm-SecureBootUEFI", "Get-Tpm",
                "Get-Service"))), \
             patch.object(sec.windows, "is_windows", return_value=True):
            report = sec.SecurityScanner().scan(ScanContext(lang="en"))
        self.assertTrue(report.skipped)
        self.assertIn("none of the security checks", report.skipped)
        self.assertEqual(report.findings, [])

    def test_unexpected_answers_do_not_crash(self):
        for answers in ({"Get-BitLockerVolume": "nije dict"},
                        {"Confirm-SecureBootUEFI": "12345"},
                        {"Get-Tpm": []},
                        {"Get-Service": {"StartType": ""}}):
            with patch.object(sec, "_ps", fake_ps(answers)), \
                 patch.object(sec.windows, "is_windows", return_value=True):
                report = sec.SecurityScanner().scan(ScanContext(lang="bs"))
            self.assertIsInstance(report.findings, list)

    def test_has_no_fix_by_policy(self):
        for fid in ("bitlocker-off", "secureboot-off", "tpm-absent",
                    "wuauserv-disabled"):
            self.assertEqual(finding_to_actions({"id": fid, "evidence": {}}), [])

    def test_messages_bilingual_and_english_clean(self):
        answers = {**ALL_GOOD, "Get-BitLockerVolume": {"Status": "Off"}}
        bs = self._scan(answers, "bs").findings[0]
        en = self._scan(answers, "en").findings[0]
        self.assertIn("BitLocker nije ukljucen", bs.title)
        self.assertIn("BitLocker is not on", en.title)
        for text in (en.title, en.why, en.impact, en.risk):
            self.assertFalse(set(BS_CHARS) & set(text.lower()), text)

    def test_unavailable_reason_is_localized(self):
        with patch.object(sec.windows, "is_windows", return_value=False):
            scanner = sec.SecurityScanner()
            self.assertIn("samo na Windowsu",
                          scanner.scan(ScanContext(lang="bs")).skipped)
            self.assertIn("only work on Windows",
                          scanner.scan(ScanContext(lang="en")).skipped)


if __name__ == "__main__":
    unittest.main()

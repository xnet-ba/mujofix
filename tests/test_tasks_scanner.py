"""Tasks scanner: autostart zadaci iz neuobicajene putanje (fake PowerShell)."""

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mujofix.scanners import tasks as tasks_mod
from mujofix.scanners.base import ScanContext

BS_CHARS = "čćžšđ"

LOGON = "MSFT_TaskLogonTrigger"
DAILY = "MSFT_TaskDailyTrigger"


def task(name, exec_path, trigger=LOGON, folder="\\", state="Ready"):
    return {"Name": name, "Path": folder, "State": state,
            "Triggers": [trigger], "Exec": [exec_path]}


class TestTasksScanner(unittest.TestCase):
    def _scan(self, tasks, lang="bs"):
        with patch.object(tasks_mod, "_tasks", return_value=tasks), \
             patch.object(tasks_mod.windows, "is_windows", return_value=True):
            return tasks_mod.TasksScanner().scan(ScanContext(lang=lang))

    def test_reports_autostart_task_outside_system_folders(self):
        report = self._scan([task("Updater", r"C:\Users\x\AppData\Updater.exe")])
        self.assertEqual(len(report.findings), 1)
        finding = report.findings[0]
        self.assertEqual(finding.id, "tasks-autostart-untrusted")
        self.assertEqual(finding.severity, "LOW")
        self.assertEqual(finding.evidence["count"], 1)
        self.assertEqual(finding.evidence["tasks"][0]["program"],
                         r"C:\Users\x\AppData\Updater.exe")
        self.assertEqual(finding.evidence["tasks"][0]["trigger"], LOGON)

    def test_ignores_trusted_locations_and_non_autostart_triggers(self):
        tasks = [
            task("WindowsThing", r"C:\Windows\System32\thing.exe"),
            task("ProgramFiles", r'"C:\Program Files\App\app.exe"'),
            task("Daily", r"C:\Users\x\AppData\Daily.exe", trigger=DAILY),
            task("Empty", ""),
        ]
        report = self._scan(tasks)
        self.assertEqual(report.findings, [])

    def test_severity_raises_with_three_or_more(self):
        tasks = [task(f"T{i}", rf"C:\Users\x\a{i}.exe") for i in range(3)]
        report = self._scan(tasks)
        self.assertEqual(report.findings[0].severity, "MEDIUM")
        self.assertEqual(report.findings[0].evidence["count"], 3)

    def test_handles_powershell_shapes(self):
        """PowerShell vrati string kad je jedan element — ne smije puci."""
        single = {"Name": "X", "Path": "\\", "State": "Ready",
                  "Triggers": LOGON, "Exec": r"C:\Users\x\x.exe"}
        report = self._scan([single])
        self.assertEqual(len(report.findings), 1)
        self.assertEqual(report.findings[0].evidence["count"], 1)

    def test_messages_are_bilingual_and_english_is_clean(self):
        bs = self._scan([task("X", r"C:\Users\x\x.exe")], "bs").findings[0]
        en = self._scan([task("X", r"C:\Users\x\x.exe")], "en").findings[0]
        self.assertIn("neuobicajene putanje", bs.title)
        self.assertIn("unusual path", en.title)
        for text in (en.title, en.why, en.impact, en.risk, en.tech_details):
            self.assertFalse(set(BS_CHARS) & set(text.lower()), text)

    def test_unavailable_reason_is_localized(self):
        with patch.object(tasks_mod.windows, "is_windows", return_value=False):
            scanner = tasks_mod.TasksScanner()
            self.assertIn("samo na Windowsu",
                          scanner.scan(ScanContext(lang="bs")).skipped)
            self.assertIn("only on Windows",
                          scanner.scan(ScanContext(lang="en")).skipped)

    def test_powershell_failure_is_a_skipped_report_not_a_crash(self):
        with patch.object(tasks_mod, "_tasks",
                          side_effect=RuntimeError("powershell nema")), \
             patch.object(tasks_mod.windows, "is_windows", return_value=True):
            report = tasks_mod.TasksScanner().scan(ScanContext(lang="en"))
        self.assertIn("scanner error", report.skipped)
        self.assertEqual(report.findings, [])


if __name__ == "__main__":
    unittest.main()

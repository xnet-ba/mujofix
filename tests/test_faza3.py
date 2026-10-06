"""Testovi Faze 3: cijeli GUI tok offscreen (scan -> odobri -> fix -> undo).

QT_QPA_PLATFORM=offscreen postavlja test-runner, ne testovi sami.
"""

import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from mujofix.actions.base import Action
from mujofix.ui.main_window import MainWindow

app = QApplication.instance() or QApplication([])


def disk_temp_finding(tmp: str) -> dict:
    return {
        "id": "disk-temp", "scanner": "disk",
        "title": "Privremeni fajlovi zauzimaju 0.0 GB",
        "why": "test", "severity": "MEDIUM", "impact": "test",
        "risk": "nizak", "reversible": True,
        "evidence": {"temp_dir": tmp, "bytes": 1, "files": 1},
        "tech_details": "walk",
    }


def unknown_finding() -> dict:
    finding = disk_temp_finding("/nonexistent")
    finding.update({"id": "misterija", "title": "Nepoznat problem",
                    "severity": "LOW"})
    return finding


class ElevatedFake(Action):
    name = "fake-elevated"
    description = "test"
    risk = "test"
    needs_elevation = True

    def precondition(self, ctx):
        return True, ""

    def snapshot(self, ctx):
        return {}

    def apply(self, ctx, state):
        raise AssertionError("elevated se ne smije pokusati")

    def verify(self, ctx, state):
        return True, ""

    def rollback(self, ctx, state):
        pass


class TestGuiFlow(unittest.TestCase):
    def make_window(self, findings: list[dict]):
        qtmp = tempfile.TemporaryDirectory()
        qdir = os.path.join(qtmp.name, "q")
        window = MainWindow(
            scan_fn=lambda: [{"scanner": "t", "findings": findings,
                              "skipped": None}],
            quarantine_dir=qdir)
        window.show()
        window.start_scan()
        window._worker.wait(5000)
        for _ in range(100):
            app.processEvents()
            if window.btn_fix.isEnabled():
                break
            time.sleep(0.02)
        return window, qtmp

    def test_summary_and_approval(self):
        window, qtmp = self.make_window(
            [disk_temp_finding("/x"), unknown_finding()])
        try:
            self.assertIn("2 problema", window.lbl_summary.text())
            self.assertEqual(window.list.count(), 2)
            # skini odobrenje s drugog nalaza
            window.list.item(1).setCheckState(Qt.Unchecked)
            approved = window.approved_findings()
            self.assertEqual([f["id"] for f in approved], ["disk-temp"])
        finally:
            window.close()
            qtmp.cleanup()

    def test_fix_then_undo_roundtrip(self):
        with tempfile.TemporaryDirectory() as data:
            window, qtmp = self.make_window([disk_temp_finding(data)])
            try:
                victim = os.path.join(data, "old.tmp")
                with open(victim, "w") as handle:
                    handle.write("podaci")
                old = time.time() - 30 * 86400
                os.utime(victim, (old, old))
                window.start_fix()
                self.assertIn("Popravljeno: 1", window.lbl_report.text())
                self.assertFalse(os.path.exists(victim))
                self.assertTrue(window.btn_undo.isEnabled())
                window.undo_all()
                with open(victim) as handle:
                    self.assertEqual(handle.read(), "podaci")
                self.assertFalse(window.btn_undo.isEnabled())
            finally:
                window.close()
                qtmp.cleanup()

    def test_no_autofix_and_elevated_skipped(self):
        from mujofix.ui import main_window as mw
        real_map = mw.finding_to_actions
        elevated = dict(disk_temp_finding("/x"))
        elevated["id"] = "fake-elevated"
        mw.finding_to_actions = lambda f: ([ElevatedFake()]
                                           if f["id"] == "fake-elevated" else [])
        try:
            window, qtmp = self.make_window([unknown_finding(), elevated])
            try:
                window.start_fix()  # nepoznat: nema akcije; elevated: UAC skip
                self.assertIn("Popravljeno: 0", window.lbl_report.text())
                self.assertIn("admin", window.log.toPlainText())
                self.assertFalse(window.btn_undo.isEnabled())
            finally:
                window.close()
                qtmp.cleanup()
        finally:
            mw.finding_to_actions = real_map


if __name__ == "__main__":
    unittest.main()

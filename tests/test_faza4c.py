"""Testovi AI-GUI spoja: explain tok (offline), consent skip, scan --out."""

import io
import json
import os
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from mujofix import cli
from mujofix.ai.mujofix_mcp import load_findings_file, STORE
from mujofix.ui.consent import ConsentDialog
from mujofix.ui.main_window import MainWindow

app = QApplication.instance() or QApplication([])


def finding() -> dict:
    return {
        "id": "disk-temp", "scanner": "disk",
        "title": "Privremeni fajlovi zauzimaju 2 GB",
        "why": "test", "severity": "MEDIUM", "impact": "test",
        "risk": "nizak", "reversible": True,
        "evidence": {"temp_dir": "/tmp", "bytes": 5},
        "tech_details": "walk",
    }


def make_window(findings: list[dict]):
    qtmp = tempfile.TemporaryDirectory()
    window = MainWindow(
        scan_fn=lambda: [{"scanner": "t", "findings": findings,
                          "skipped": None}],
        quarantine_dir=os.path.join(qtmp.name, "q"))
    window.show()
    window.start_scan()
    window._worker.wait(5000)
    for _ in range(100):
        app.processEvents()
        if window.btn_fix.isEnabled():
            break
        time.sleep(0.02)
    return window, qtmp


class TestExplainFlow(unittest.TestCase):
    def setUp(self):
        QSettings("MujoFix", "ai").setValue(ConsentDialog.SETTINGS_KEY, "on")

    def tearDown(self):
        QSettings("MujoFix", "ai").remove(ConsentDialog.SETTINGS_KEY)

    def test_explain_shows_offline_text_and_enables_sent(self):
        window, qtmp = make_window([finding()])
        try:
            self.assertTrue(window.btn_explain.isEnabled())
            window.explain_findings()  # bez dijaloga (choice vec postavljen)
            log = window.log.toPlainText()
            self.assertIn("Privremeni fajlovi", log)
            self.assertIn("[AI: offline]", log)
            self.assertTrue(window.btn_sent.isEnabled())
            self.assertEqual(len(window._chain.sent_log), 1)
        finally:
            window.close()
            qtmp.cleanup()

    def test_no_consent_blocks_nothing_but_logs(self):
        QSettings("MujoFix", "ai").remove(ConsentDialog.SETTINGS_KEY)
        self.assertIsNone(ConsentDialog.stored_choice())


class TestScanOut(unittest.TestCase):
    def test_out_file_feeds_mcp(self):
        buf = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "findings.json")
            with redirect_stdout(buf):
                with patch("mujofix.platform.windows.is_windows",
                           return_value=False):
                    cli.main(["scan", "--scanner", "disk", "--out", out])
            with open(out, encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertIn("findings", payload)
            self.assertIn("system_info", payload)
            load_findings_file(out)
            self.assertEqual(STORE["findings"], payload["findings"])
            STORE["findings"] = []
            STORE["system_info"] = None


if __name__ == "__main__":
    unittest.main()

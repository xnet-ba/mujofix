"""Testovi Faze 4b: MCP s pravim podacima (pravi stdio roundtrip), pristanak,
validator cap. Offscreen za dijaloge."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PySide6.QtWidgets import (QApplication, QDialog, QLabel,
                               QPushButton)

from mujofix.ai.mujofix_mcp import MAX_PLAN_STEPS, validate_plan
from mujofix.ui.consent import ConsentDialog, SentLogViewer

app = QApplication.instance() or QApplication([])

MCP = os.path.join(os.path.dirname(__file__), "..", "mujofix", "ai",
                   "mujofix_mcp.py")


def mcp_session(messages: list[dict], findings_path: str | None = None,
                timeout_s: int = 30) -> list[dict]:
    """Posalji NDJSON zahtjeve pravom MCP procesu, vrati odgovore."""
    cmd = [sys.executable, os.path.abspath(MCP)]
    if findings_path:
        cmd += ["--findings", findings_path]
    body = "".join(json.dumps(m) + "\n" for m in messages)
    proc = subprocess.run(cmd, input=body, capture_output=True, text=True,
                          timeout=timeout_s)
    if proc.returncode != 0:
        raise RuntimeError(f"MCP pao: {proc.stderr[-500:]}")
    return [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]


def rpc(msg_id: int, method: str, params: dict | None = None) -> dict:
    msg: dict = {"jsonrpc": "2.0", "id": msg_id, "method": method}
    if params is not None:
        msg["params"] = params
    return msg


class TestMcpRealData(unittest.TestCase):
    def test_findings_and_evidence_roundtrip(self):
        store = {"findings": [
            {"id": "disk-temp", "title": "Temp 2GB",
             "evidence": {"bytes": 2000}}],
            "system_info": {"os": "Windows"}}
        with tempfile.NamedTemporaryFile("w", suffix=".json",
                                         delete=False) as handle:
            json.dump(store, handle)
            path = handle.name
        try:
            resp = mcp_session([
                rpc(1, "initialize"),
                rpc(2, "tools/list"),
                rpc(3, "tools/call", {"name": "get_findings",
                                      "arguments": {}}),
                rpc(4, "tools/call", {"name": "get_evidence",
                                      "arguments": {"finding_id": "disk-temp"}}),
                rpc(5, "tools/call", {"name": "get_evidence",
                                      "arguments": {"finding_id": "nepostojeci"}}),
            ], findings_path=path)
        finally:
            os.unlink(path)
        by_id = {r["id"]: r["result"] for r in resp}
        self.assertEqual(by_id[1]["serverInfo"]["name"], "mujofix")
        self.assertEqual(len(by_id[2]["tools"]), 5)
        self.assertEqual(by_id[3]["findings"][0]["id"], "disk-temp")
        self.assertEqual(by_id[4]["evidence"], {"bytes": 2000})
        self.assertIn("error", by_id[5])

    def test_propose_plan_accept_and_reject_live(self):
        good = {"steps": [{"action": "clean_temp", "target": "C:\\T"}]}
        evil = {"steps": [{"action": "clean_temp",
                           "target": "C:\\Windows\\System32\\x"}]}
        resp = mcp_session([
            rpc(1, "tools/call", {"name": "propose_plan",
                                  "arguments": {"plan": good}}),
            rpc(2, "tools/call", {"name": "propose_plan",
                                  "arguments": {"plan": evil}}),
        ])
        self.assertTrue(resp[0]["result"]["ok"])
        self.assertIn("error", resp[1])
        self.assertIn("zasticena", resp[1]["error"]["message"])


class TestValidatorHardening(unittest.TestCase):
    def test_too_many_steps_rejected(self):
        plan = {"steps": [{"action": "clean_temp", "target": f"T{i}"}
                          for i in range(MAX_PLAN_STEPS + 1)]}
        ok, reason = validate_plan(plan)
        self.assertFalse(ok)
        self.assertIn("previse koraka", reason)

    def test_empty_action_rejected(self):
        ok, _ = validate_plan({"steps": [{"action": "", "target": "T"}]})
        self.assertFalse(ok)

    def test_exactly_max_accepted(self):
        plan = {"steps": [{"action": "clean_temp", "target": f"T{i}"}
                          for i in range(MAX_PLAN_STEPS)]}
        ok, _ = validate_plan(plan)
        self.assertTrue(ok)


class TestConsent(unittest.TestCase):
    def test_accept_reject_paths(self):
        dlg = ConsentDialog({"a": 1})
        dlg.accept()
        self.assertEqual(dlg.result(), QDialog.Accepted)
        dlg2 = ConsentDialog({"a": 1})
        dlg2.reject()
        self.assertEqual(dlg2.result(), QDialog.Rejected)

    def test_stored_choice_roundtrip(self):
        dlg = ConsentDialog({"a": 1})
        dlg.chk_remember.setChecked(True)
        dlg.accept()
        self.assertEqual(ConsentDialog.stored_choice(), "on")
        dlg2 = ConsentDialog({"a": 1})
        dlg2.reject()
        self.assertEqual(ConsentDialog.stored_choice(), "off")

    def test_consent_text_states_confirmed_zen(self):
        from mujofix.ui.consent import CATEGORIES_BS
        self.assertIn("POTVRDJENO", CATEGORIES_BS)
        self.assertNotIn("NEPOTVR", CATEGORIES_BS)
        self.assertIn("opencode.ai/legal/terms-of-service", CATEGORIES_BS)
        self.assertIn("opencode.ai/v2/docs/console/models/", CATEGORIES_BS)

    def test_sent_log_viewer_builds(self):
        from PySide6.QtWidgets import QPlainTextEdit
        viewer = SentLogViewer([{"findings": []}])
        view = viewer.findChild(QPlainTextEdit)
        self.assertIn("findings", view.toPlainText())
        viewer.close()


    def test_english_consent_dialog_is_translated(self):
        from mujofix.ui.consent import ConsentDialog
        dlg = ConsentDialog("primjer", lang="en")
        try:
            self.assertIn("consent", dlg.windowTitle().lower())
            texts = [b.text() for b in dlg.findChildren(QPushButton)]
            self.assertIn("I accept AI", texts)
            self.assertIn("Stay offline", texts)
            labels = " ".join(lb.text() for lb in dlg.findChildren(QLabel))
            self.assertIn("SENT (anonymized)", labels)
            self.assertNotIn("Šalje se", labels)
            self.assertNotIn("Ostajem", labels)
        finally:
            dlg.close()


class TestQuarantineDialog(unittest.TestCase):
    """Vracanje fajlova iz karantina (i iz RANIJIH sesija) iz GUI-ja."""

    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication

        cls.app = QApplication.instance() or QApplication([])

    def _dialog(self, tmp):
        from mujofix.ui.quarantine import QuarantineDialog

        return QuarantineDialog(tmp, lang="bs")

    def test_lists_restores_and_handles_unknown_source(self):
        import time
        from unittest.mock import patch

        from PySide6.QtWidgets import QMessageBox

        from mujofix.actions.base import quarantine_file, save_manifest

        with tempfile.TemporaryDirectory() as tmp:
            qdir = os.path.join(tmp, "q")
            known = os.path.join(tmp, "known.txt")
            with open(known, "wb") as handle:
                handle.write(b"aaa")
            record = quarantine_file(known, qdir)
            save_manifest(qdir, "temp-manifest", [record])
            unknown_src = os.path.join(tmp, "unknown.txt")
            with open(unknown_src, "wb") as handle:
                handle.write(b"b")
            quarantine_file(unknown_src, qdir)  # bez manifesta

            dialog = self._dialog(qdir)
            try:
                self.assertEqual(dialog.list.count(), 2)
                self.assertIn("2 fajlova", dialog.info.text())
                # nadji red sa poznatim originalom i vrati ga
                for row in range(dialog.list.count()):
                    dialog.list.setCurrentRow(row)
                    if dialog.btn_restore.isEnabled():
                        break
                with patch.object(QMessageBox, "information"):
                    dialog.restore_selected()
                self.assertTrue(os.path.exists(known))
                self.assertEqual(dialog.list.count(), 1)  # refresh
                # preostali je bez originala -> vrati je onemoguceno
                dialog.list.setCurrentRow(0)
                self.assertIsNone(dialog._entries[0]["original"])
                self.assertFalse(dialog.btn_restore.isEnabled())
            finally:
                dialog.close()

    def test_delete_selected_aspect(self):
        from unittest.mock import patch

        from PySide6.QtWidgets import QMessageBox

        from mujofix.actions.base import quarantine_file

        with tempfile.TemporaryDirectory() as tmp:
            qdir = os.path.join(tmp, "q")
            src = os.path.join(tmp, "x.tmp")
            with open(src, "wb") as handle:
                handle.write(b"x")
            quarantine_file(src, qdir)
            dialog = self._dialog(qdir)
            try:
                self.assertEqual(dialog.list.count(), 1)
                dialog.list.setCurrentRow(0)  # bez selekcije nema akcije
                with patch.object(QMessageBox, "question",
                                  return_value=QMessageBox.Yes):
                    dialog.delete_selected()
                self.assertEqual(dialog.list.count(), 0)
                self.assertIn("0 fajlova", dialog.info.text())
                self.assertFalse(dialog.btn_delete.isEnabled())
            finally:
                dialog.close()


if __name__ == "__main__":
    unittest.main()

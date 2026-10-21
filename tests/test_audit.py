"""JSON dnevnik izvrsavanja: putanja, zapis i citljivost."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mujofix import audit


class TestAudit(unittest.TestCase):
    def test_path_has_timestamp_and_parent(self):
        path = audit.audit_path("/tmp/x")
        name = os.path.basename(path)
        self.assertTrue(name.startswith("audit-") and name.endswith(".json"))
        self.assertEqual(len(name), len("audit-YYYYmmdd-HHMMSS.json"))

    def test_record_marks_dry_run(self):
        apply = audit.build_record([{"action": "a"}], {"ok": 1}, False)
        dry = audit.build_record([], {"ok": 0}, True)
        self.assertEqual(apply["mode"], "apply")
        self.assertEqual(dry["mode"], "dry-run")
        self.assertIn("when", apply)
        self.assertEqual(apply["summary"], {"ok": 1})

    def test_write_creates_valid_readable_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = audit.audit_path(os.path.join(tmp, "audit"))
            audit.write_record(path, audit.build_record(
                [{"action": "clean_temp", "phase": "done", "ok": True,
                  "message": "200 MB"}], {"ok": 1}, False))
            record = json.load(open(path, encoding="utf-8"))
            self.assertEqual(record["steps"][0]["action"], "clean_temp")
            text = open(path, encoding="utf-8").read()
            self.assertIn("\n", text)  # indentovan, citljiv


if __name__ == "__main__":
    unittest.main()

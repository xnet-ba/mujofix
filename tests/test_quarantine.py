"""Karantin: velicina u zapisu, mjerenje zauzeca i trajno ciscenje."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mujofix.actions.base import (
    ActionContext,
    Runner,
    purge_quarantine,
    quarantine_file,
    quarantine_usage,
)
from mujofix.actions.temp import CleanTemp


def _old_file(directory: str, name: str, content: bytes, days: int = 31) -> str:
    import time

    path = os.path.join(directory, name)
    with open(path, "wb") as handle:
        handle.write(content)
    old = time.time() - days * 86400
    os.utime(path, (old, old))
    return path


class TestQuarantine(unittest.TestCase):
    def test_record_keeps_size_before_move(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "a.tmp")
            with open(src, "wb") as handle:
                handle.write(b"1234567890")
            record = quarantine_file(src, os.path.join(tmp, "q"))
            self.assertEqual(record["size"], 10)
            self.assertFalse(os.path.exists(src))  # premjesten, ne obrisan
            self.assertTrue(os.path.exists(record["quarantined"]))

    def test_usage_counts_files_and_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            qdir = os.path.join(tmp, "q")
            self.assertEqual(quarantine_usage(qdir), (0, 0))  # ne postoji
            os.makedirs(qdir)
            with open(os.path.join(qdir, "x"), "wb") as handle:
                handle.write(b"x" * 100)
            with open(os.path.join(qdir, "x-manifest.json"), "w") as handle:
                json.dump([{"a": 1}], handle)
            files, total = quarantine_usage(qdir)
            self.assertEqual(files, 2)
            self.assertEqual(total, 100 + os.path.getsize(
                os.path.join(qdir, "x-manifest.json")))

    def test_purge_removes_everything_and_reports_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            qdir = os.path.join(tmp, "q")
            os.makedirs(qdir)
            with open(os.path.join(qdir, "x"), "wb") as handle:
                handle.write(b"x" * 200)
            with open(os.path.join(qdir, "m.json"), "w") as handle:
                handle.write("[]")
            before = quarantine_usage(qdir)[1]
            files, freed = purge_quarantine(qdir)
            self.assertEqual(files, 2)
            self.assertEqual(freed, before)
            self.assertEqual(os.listdir(qdir), [])  # prazno
            self.assertEqual(quarantine_usage(qdir), (0, 0))
            # idempotentno: drugi poziv ne pada i ne vraca nista
            self.assertEqual(purge_quarantine(qdir), (0, 0))

    def test_fix_then_purge_frees_exactly_what_was_moved(self):
        """Cijeli tok: popravka -> mjerenje -> ciscenje daje iste bajtove."""
        with tempfile.TemporaryDirectory() as data, \
                tempfile.TemporaryDirectory() as qdir:
            payload = b"z" * 4096
            _old_file(data, "old.tmp", payload)
            _old_file(data, "old2.tmp", payload)
            ctx = ActionContext(quarantine_dir=qdir)
            result = Runner().run(CleanTemp(data), ctx)
            self.assertTrue(result.ok and result.verified, result.message)
            files, total = quarantine_usage(qdir)
            self.assertEqual(files, 3)  # 2 fajla + manifest
            self.assertGreaterEqual(total, 2 * len(payload))
            deleted, freed = purge_quarantine(qdir)
            self.assertEqual(deleted, 3)
            self.assertEqual(freed, total)


if __name__ == "__main__":
    unittest.main()

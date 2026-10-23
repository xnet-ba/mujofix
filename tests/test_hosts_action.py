"""Akcija `remove_hosts_entry`: apply -> verify -> rollback -> identicno stanje."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mujofix.actions.base import ActionContext, Runner
from mujofix.actions.hosts import RemoveHostsEntry
from mujofix.actions.mapping import finding_to_actions

BS_CHARS = "čćžšđ"

HOSTS = """# hosts fajl
127.0.0.1   localhost
10.0.0.1    zlonamjerni.test   # hijack
192.168.0.10 nas-server
"""


def _write(tmp: str, text: str = HOSTS) -> str:
    path = os.path.join(tmp, "hosts")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return path


class TestRemoveHostsEntry(unittest.TestCase):
    def test_apply_verify_rollback_restores_identical_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp)
            original = open(path, encoding="utf-8").read()
            ctx = ActionContext(quarantine_dir=os.path.join(tmp, "q"))
            action = RemoveHostsEntry(path, "10.0.0.1", "zlonamjerni.test")

            result = Runner().run(action, ctx)
            self.assertTrue(result.ok and result.verified, result.message)
            after = open(path, encoding="utf-8").read()
            self.assertNotIn("zlonamjerni.test", after)
            # sve ostalo je netaknuto (komentari, ostali zapisi, prazni redovi)
            self.assertIn("# hosts fajl", after)
            self.assertIn("127.0.0.1   localhost", after)
            self.assertIn("192.168.0.10 nas-server", after)
            self.assertEqual(len(after.splitlines()),
                             len(original.splitlines()) - 1)

            action.rollback(ctx, result.state)
            self.assertEqual(open(path, encoding="utf-8").read(), original)

    def test_removes_only_the_reported_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp, "1.2.3.4 a.test\n5.6.7.8 b.test\n")
            ctx = ActionContext(quarantine_dir=os.path.join(tmp, "q"))
            Runner().run(RemoveHostsEntry(path, "1.2.3.4", "a.test"), ctx)
            left = open(path, encoding="utf-8").read()
            self.assertNotIn("1.2.3.4", left)
            self.assertIn("5.6.7.8 b.test", left)

    def test_precondition_refuses_when_entry_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp)
            ctx = ActionContext(quarantine_dir=os.path.join(tmp, "q"))
            ok, reason = RemoveHostsEntry(path, "9.9.9.9", "nema.test"
                                          ).precondition(ctx)
            self.assertFalse(ok)
            self.assertIn("9.9.9.9", reason)

    def test_missing_file_is_refused_not_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = ActionContext(quarantine_dir=tmp)
            result = Runner().run(
                RemoveHostsEntry(os.path.join(tmp, "nema"), "1.1.1.1", "x"),
                ctx)
            self.assertFalse(result.ok)
            self.assertIn("precondition", result.message)

    def test_needs_elevation_because_hosts_is_protected(self):
        self.assertTrue(RemoveHostsEntry("/x", "1", "h").needs_elevation)

    def test_messages_are_bilingual(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp)
            action = RemoveHostsEntry(path, "10.0.0.1", "zlonamjerni.test")
            bs = action.precondition(
                ActionContext(quarantine_dir=tmp, lang="bs"))[1]
            en = action.precondition(
                ActionContext(quarantine_dir=tmp, lang="en"))[1]
            self.assertIn("je u hosts fajlu", bs)
            self.assertIn("is in the hosts file", en)
            self.assertFalse(set(BS_CHARS) & set(en.lower()))

    def test_mapping_creates_one_action_per_suspicious_entry(self):
        finding = {
            "id": "network-hosts", "scanner": "network",
            "evidence": {"path": "/etc/hosts",
                         "entries": [["10.0.0.1", "a.test"],
                                     ["10.0.0.2", "b.test"]]},
        }
        actions = finding_to_actions(finding)
        self.assertEqual([a.name for a in actions],
                         ["remove_hosts_entry"] * 2)
        self.assertEqual([(a.ip, a.host) for a in actions],
                         [("10.0.0.1", "a.test"), ("10.0.0.2", "b.test")])

    def test_mapping_ignores_other_findings(self):
        self.assertEqual(finding_to_actions(
            {"id": "network-dns", "scanner": "network",
             "evidence": {"host": "x"}}), [])

    def test_falls_back_to_copy_when_replace_is_denied(self):
        """Hardenovan Windows (WDAC/ASR) zabranjuje os.replace nad hosts-om.

        Dokazano na Win11 Enterprise N: os.replace -> WinError 5, a copyfile radi.
        Akcija mora i tada da odradi posao (i rollback).
        """
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp)
            original = open(path, encoding="utf-8").read()
            ctx = ActionContext(quarantine_dir=os.path.join(tmp, "q"))
            action = RemoveHostsEntry(path, "10.0.0.1", "zlonamjerni.test")
            with patch("mujofix.actions.hosts.os.replace",
                       side_effect=PermissionError(13, "Access is denied")):
                result = Runner().run(action, ctx)
            self.assertTrue(result.ok and result.verified, result.message)
            after = open(path, encoding="utf-8").read()
            self.assertNotIn("zlonamjerni.test", after)
            self.assertIn("127.0.0.1   localhost", after)
            # rollback mora vratiti original (i on ide kroz isti fallback)
            with patch("mujofix.actions.hosts.os.replace",
                       side_effect=PermissionError(13, "Access is denied")):
                action.rollback(ctx, result.state)
            self.assertEqual(open(path, encoding="utf-8").read(), original)

    def test_preserves_crlf_and_is_byte_identical_after_rollback(self):
        """Windows hosts je CRLF — rollback mora vratiti BAJT-identicno."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "hosts")
            original = (b"# header\r\n"
                        b"127.0.0.1   localhost\r\n"
                        b"10.0.0.1    zlonamjerni.test   # hijack\r\n"
                        b"# bez trailing newline")
            with open(path, "wb") as handle:
                handle.write(original)
            ctx = ActionContext(quarantine_dir=os.path.join(tmp, "q"))
            action = RemoveHostsEntry(path, "10.0.0.1", "zlonamjerni.test")
            result = Runner().run(action, ctx)
            self.assertTrue(result.ok and result.verified, result.message)
            after = open(path, "rb").read()
            self.assertNotIn(b"zlonamjerni.test", after)
            self.assertIn(b"\r\n", after)          # CRLF sacuvan
            self.assertNotIn(b"\n\n", after)
            self.assertTrue(after.endswith(b"# bez trailing newline"))
            action.rollback(ctx, result.state)
            self.assertEqual(open(path, "rb").read(), original)  # BAJT-identicno


if __name__ == "__main__":
    unittest.main()

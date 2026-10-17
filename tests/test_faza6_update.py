"""Testovi Faze 6: auto-update logika (bez mreze).

Pravi mrezni put i pokretanje preuzetog artefakta su netestirani (bez VM-a);
sve ostalo je pokriveno s ubacenim (fake) fetch/download funkcijama.
"""

import contextlib
import hashlib
import io
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mujofix import update
from mujofix.platform import windows


def _release(tag, names):
    return {"tag": tag, "assets": [
        {"name": name, "url": f"https://x/{name}", "size": 10}
        for name in names]}


class _FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class TestVersionCompare(unittest.TestCase):
    def test_is_newer(self):
        self.assertTrue(update.is_newer("v0.2.0", "0.1.0"))
        self.assertTrue(update.is_newer("1.0.0", "0.1.0"))
        self.assertFalse(update.is_newer("v0.1.0", "0.1.0"))
        self.assertFalse(update.is_newer("v0.0.9", "0.1.0"))

    def test_bad_version_raises(self):
        with self.assertRaises(update.UpdateError):
            update.is_newer("nema-broja", "0.1.0")


class TestAssetPick(unittest.TestCase):
    def test_prefers_installer_over_zip(self):
        assets = [{"name": "MujoFix-v0.2.0.zip", "url": "a", "size": 1},
                  {"name": "SHA256SUMS.txt", "url": "b", "size": 1},
                  {"name": "MujoFixSetup.exe", "url": "c", "size": 1}]
        self.assertEqual(update.pick_asset(assets)["name"], "MujoFixSetup.exe")

    def test_falls_back_to_zip_and_skips_sums(self):
        assets = [{"name": "SHA256SUMS.txt", "url": "b", "size": 1},
                  {"name": "MujoFix-v0.2.0.zip", "url": "a", "size": 1}]
        self.assertEqual(update.pick_asset(assets)["name"], "MujoFix-v0.2.0.zip")

    def test_only_sums_returns_none(self):
        self.assertIsNone(update.pick_asset(
            [{"name": "SHA256SUMS.txt", "url": "b", "size": 1}]))


class TestSums(unittest.TestCase):
    def test_parse(self):
        text = ("a" * 64 + "  MujoFix-v0.2.0.zip\n"
                + "d" * 64 + " *drugi.bin\n"
                + "smece\n")
        sums = update.parse_sha256sums(text)
        self.assertEqual(sums["MujoFix-v0.2.0.zip"], "a" * 64)
        self.assertEqual(sums["drugi.bin"], "d" * 64)
        self.assertEqual(len(sums), 2)


class TestCheck(unittest.TestCase):
    def test_available(self):
        info = update.check_for_update(
            current="0.1.0",
            fetch=lambda url: _release("v0.2.0", ["MujoFix-v0.2.0.zip"]))
        self.assertTrue(info["available"])
        self.assertEqual(info["latest"], "0.2.0")
        self.assertEqual(info["asset"]["name"], "MujoFix-v0.2.0.zip")

    def test_not_available(self):
        info = update.check_for_update(
            current="0.2.0", fetch=lambda url: _release("v0.2.0", ["x.zip"]))
        self.assertFalse(info["available"])
        self.assertIsNone(info["asset"])


class TestDownload(unittest.TestCase):
    def test_download_verifies_sha(self):
        payload = b"podaci"
        sha = hashlib.sha256(payload).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            dest = os.path.join(tmp, "f.zip")
            with patch.object(update.urllib.request, "urlopen",
                              return_value=_FakeResponse(payload)):
                out = update.download("https://x/f.zip", dest, sha)
            self.assertEqual(out, dest)
            self.assertTrue(os.path.exists(dest))

    def test_sha_mismatch_removes_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = os.path.join(tmp, "f.zip")
            with patch.object(update.urllib.request, "urlopen",
                              return_value=_FakeResponse(b"podaci")):
                with self.assertRaises(update.UpdateError):
                    update.download("https://x/f.zip", dest, "0" * 64)
            self.assertFalse(os.path.exists(dest))


class TestApply(unittest.TestCase):
    def test_apply_uses_sums_and_launches(self):
        assets = [{"name": "MujoFix-v0.2.0.zip", "url": "https://x/z", "size": 1},
                  {"name": "SHA256SUMS.txt", "url": "https://x/sums", "size": 1}]
        info = {"available": True, "asset": assets[0], "assets": assets}
        sums = "a" * 64 + "  MujoFix-v0.2.0.zip\n"
        launched = []

        def fake_download(url, dest, sha):
            with open(dest, "wb") as handle:
                handle.write(b"x")
            return dest

        with tempfile.TemporaryDirectory() as tmp:
            result = update.apply_update(
                info, workdir=tmp, download_fn=fake_download,
                launch_fn=lambda path: (launched.append(path), True)[1],
                fetch_text_fn=lambda url: sums)
        self.assertTrue(result["launched"])
        self.assertEqual(result["sha256"], "a" * 64)
        self.assertTrue(launched)

    def test_apply_without_asset_raises(self):
        with self.assertRaises(update.UpdateError):
            update.apply_update({"asset": None})


class TestLaunch(unittest.TestCase):
    def test_launch_off_windows_unsupported(self):
        if windows.is_windows():
            self.skipTest("samo ne-Windows grana")
        with self.assertRaises(windows.NotSupported):
            update.launch_artifact("/tmp/x.exe")


class TestVersionSource(unittest.TestCase):
    def test_current_version_reads_changelog(self):
        from mujofix.version import current_version
        self.assertRegex(current_version(), r"^\d+\.\d+\.\d+$")


class TestUpdateCli(unittest.TestCase):
    def test_no_update_reports_current(self):
        from mujofix import cli
        out = io.StringIO()
        with patch.object(cli.update_mod, "check_for_update",
                          return_value={"available": False, "current": "0.1.0"}):
            with contextlib.redirect_stdout(out):
                rc = cli.main(["update"])
        self.assertEqual(rc, 0)
        self.assertIn("najnovija", out.getvalue())

    def test_apply_reports_error(self):
        from mujofix import cli
        out = io.StringIO()
        with patch.object(cli.update_mod, "check_for_update",
                          return_value={"available": True, "current": "0.1.0",
                                        "latest": "0.2.0"}):
            with patch.object(cli.update_mod, "apply_update",
                              side_effect=cli.update_mod.UpdateError("boom")):
                with contextlib.redirect_stdout(out):
                    rc = cli.main(["update", "--apply"])
        self.assertEqual(rc, 1)
        self.assertIn("boom", out.getvalue())


if __name__ == "__main__":
    unittest.main()

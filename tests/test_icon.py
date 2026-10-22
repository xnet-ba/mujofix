"""Ikona aplikacije: ICO je validan i stvarno povezan u build i installer."""

import os
import struct
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

ROOT = os.path.join(os.path.dirname(__file__), "..")
ICON = os.path.join(ROOT, "assets", "mujofix.ico")


class TestIconFile(unittest.TestCase):
    def setUp(self):
        self.data = open(ICON, "rb").read()

    def test_header_is_valid_ico(self):
        reserved, kind, count = struct.unpack("<HHH", self.data[:6])
        self.assertEqual((reserved, kind), (0, 1))  # 1 = ICO
        self.assertGreaterEqual(count, 4)
        self.assertEqual(len(self.data[6:]) >= 16 * count, True)

    def test_every_entry_has_png_payload_and_expected_size(self):
        count = struct.unpack("<H", self.data[4:6])[0]
        offset = 6
        sizes, images = [], []
        for _ in range(count):
            w, h, _colors, _res, planes, bits, size, pos = struct.unpack(
                "<BBBBHHII", self.data[offset:offset + 16])
            offset += 16
            png = self.data[pos:pos + size]
            self.assertEqual(planes, 1)
            self.assertEqual(bits, 32)
            self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n", "nije PNG payload")
            sizes.append(w or 256)
            images.append((w or 256, h or 256))
        self.assertIn(16, sizes)   # mala ikona za taskbar/tray
        self.assertIn(256, sizes)  # velika za explorer
        self.assertTrue(all(w == h for w, h in images), "ikona mora biti kvadrat")

    def test_generator_script_is_reproducible(self):
        """make_icon.py mora postojati (da se ikona moze regenerisati)."""
        self.assertTrue(os.path.isfile(
            os.path.join(ROOT, "scripts", "make_icon.py")))


class TestReadmeScreenshots(unittest.TestCase):
    """Linkovi iz README-a ne smiju voditi u 404."""

    def test_screenshots_exist_and_are_links_in_readme(self):
        import re

        for name in ("mujofix-light.png", "mujofix-dark.png"):
            path = os.path.join(ROOT, "docs", "screenshots", name)
            self.assertTrue(os.path.isfile(path), f"nema {name}")
            self.assertGreater(os.path.getsize(path), 5000)
        for readme in ("README.md", "README.en.md"):
            text = open(os.path.join(ROOT, readme), encoding="utf-8").read()
            for ref in re.findall(r'src="(docs/screenshots/[^"]+)"', text):
                self.assertTrue(
                    os.path.isfile(os.path.join(ROOT, ref)),
                    f"{readme} linkuje nepostojeci {ref}")

    def test_generator_script_exists(self):
        self.assertTrue(os.path.isfile(
            os.path.join(ROOT, "scripts", "make_screenshots.py")))


class TestIconWiring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication

        cls.app = QApplication.instance() or QApplication([])

    def test_spec_uses_the_icon_for_both_exes(self):
        text = open(os.path.join(ROOT, "mujofix.spec"), encoding="utf-8").read()
        self.assertEqual(text.count('icon="assets/mujofix.ico"'), 2)
        self.assertNotIn('icon="NONE"', text)
        self.assertIn('("assets", "assets")', text)  # ikona ide u bundle

    def test_installer_paths_exist_relative_to_source_dir(self):
        """Inno rjesava [Setup]/[Files] putanje relativno na SourceDir.

        CI je pao jer je SetupIconFile bio "..\assets\..." — van repo root-a.
        Ovaj test rjesava svaku putanju kako Inno to radi i trazi da postoji.
        """
        import re

        iss_dir = os.path.join(ROOT, "installer")
        text = open(os.path.join(iss_dir, "mujofix.iss"),
                    encoding="utf-8").read()
        source_dir = re.search(r"^SourceDir=(.+)$", text, re.M).group(1).strip()
        base = os.path.normpath(os.path.join(iss_dir, source_dir))
        self.assertEqual(os.path.normpath(base), os.path.normpath(ROOT))

        icon = re.search(r"^SetupIconFile=(.+)$", text, re.M).group(1).strip()
        icon_path = os.path.join(base, icon.replace('\\', os.sep))
        self.assertTrue(os.path.isfile(icon_path),
                        f"SetupIconFile ne postoji: {icon}")
        for src in re.findall(r'^Source: "([^"]+)"', text, re.M):
            if src.startswith("dist"):  # build artefakt, ne postoji u repou
                continue
            path = os.path.join(base, src.replace('\\', os.sep))
            self.assertTrue(os.path.isfile(path),
                            f"Source ne postoji: {src}")

    def test_theme_exposes_icon(self):
        from PySide6.QtGui import QIcon

        from mujofix.ui import theme

        icon = theme.app_icon()
        self.assertIsInstance(icon, QIcon)
        self.assertFalse(icon.isNull())
        self.assertIn(16, [size.width() for size in icon.availableSizes()])


if __name__ == "__main__":
    unittest.main()

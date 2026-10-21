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


class TestIconWiring(unittest.TestCase):
    def test_spec_uses_the_icon_for_both_exes(self):
        text = open(os.path.join(ROOT, "mujofix.spec"), encoding="utf-8").read()
        self.assertEqual(text.count('icon="assets/mujofix.ico"'), 2)
        self.assertNotIn('icon="NONE"', text)
        self.assertIn('("assets", "assets")', text)  # ikona ide u bundle

    def test_installer_uses_the_icon(self):
        text = open(os.path.join(ROOT, "installer", "mujofix.iss"),
                    encoding="utf-8").read()
        self.assertIn(r"SetupIconFile=..\assets\mujofix.ico", text)

    def test_theme_exposes_icon(self):
        from PySide6.QtGui import QIcon

        from mujofix.ui import theme

        icon = theme.app_icon()
        self.assertIsInstance(icon, QIcon)
        self.assertFalse(icon.isNull())
        self.assertIn(16, [size.width() for size in icon.availableSizes()])


if __name__ == "__main__":
    unittest.main()

"""i18n cuvar: nepostojeci kljuc se u UI prikaze kao sirovo ime kljuca."""

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mujofix.i18n.strings import STRINGS, tr


class TestStrings(unittest.TestCase):
    def test_bs_and_en_have_the_same_keys(self):
        self.assertEqual(set(STRINGS["bs"]), set(STRINGS["en"]))

    def test_no_empty_translations(self):
        for lang, table in STRINGS.items():
            for key, text in table.items():
                self.assertTrue(text.strip(), f"{lang}.{key} je prazan")

    def test_every_key_used_in_ui_exists(self):
        """`tr("...")` i `self._t("...")` moraju imati prijevod."""
        root = os.path.join(os.path.dirname(__file__), "..", "mujofix")
        used = set()
        for base, _dirs, files in os.walk(root):
            for name in files:
                if not name.endswith(".py"):
                    continue
                with open(os.path.join(base, name), encoding="utf-8") as fh:
                    src = fh.read()
                used |= set(re.findall(r'(?:_t|tr)\(\s*"([a-z0-9_]+)"', src))
        missing = sorted(k for k in used if k not in STRINGS["bs"])
        self.assertEqual(missing, [], f"kljucevi bez prijevoda: {missing}")

    def test_unknown_key_falls_back_to_key(self):
        self.assertEqual(tr("nema_ovog_kljuca", "bs"), "nema_ovog_kljuca")

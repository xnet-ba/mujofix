"""Cuvar lokalizacije teksta nalaza (scanneri pisu preko `t(ctx, key)`).

Ratchet: `MIGRATED` je lista scannera koji su prevedeni. Kad se scanner
migrira, dodaj ga ovdje — tako novi bosanski tekst ne moze uci u vec
migriran scanner, a lista se smanjuje dok svi ne budu gotovi.
"""

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mujofix.i18n.strings import STRINGS
from mujofix.scanners.base import ScanContext

ROOT = os.path.join(os.path.dirname(__file__), "..")
SCANNERS = os.path.join(ROOT, "mujofix", "scanners")
BS_CHARS = "čćžšđ"

# Scanner-i koji su kompletno prevedeni (tekst ide kroz `t(ctx, ...)`).
MIGRATED = {"disk"}
# Polja nalaza koja su korisniku vidljiva.
FIELDS = ("title", "why", "impact", "risk")


def _text_literals(source: str) -> list[str]:
    """String literali koji se predaju kao title/why/impact/risk."""
    out = []
    for field in FIELDS:
        for match in re.finditer(rf"{field}\s*=\s*(f?)(\"[^\"]*\"|'[^']*')",
                                 source):
            out.append(match.group(2))
    return out


class TestScannerText(unittest.TestCase):
    def test_english_scanner_keys_have_no_bosnian_diacritics(self):
        bad = [(key, text) for key, text in STRINGS["en"].items()
               if key.startswith("sc_") and set(BS_CHARS) & set(text.lower())]
        self.assertEqual(bad, [], f"bosanski znakovi u EN tekstu: {bad}")

    def test_scanner_keys_exist_in_both_languages(self):
        bs = {k for k in STRINGS["bs"] if k.startswith("sc_")}
        en = {k for k in STRINGS["en"] if k.startswith("sc_")}
        self.assertEqual(bs, en)
        self.assertTrue(bs, "nema sc_ kljuceva")

    def test_migrated_scanners_have_no_hardcoded_bosnian_findings(self):
        for name in sorted(MIGRATED):
            source = open(os.path.join(SCANNERS, f"{name}.py"),
                          encoding="utf-8").read()
            leaked = [lit for lit in _text_literals(source)
                      if set(BS_CHARS) & set(lit.lower())]
            self.assertEqual(leaked, [],
                             f"{name}.py ima hardkodovan tekst: {leaked}")

    def test_disk_scanner_renders_in_both_languages(self):
        """Deterministicki: lazni disk_usage -> isti nalaz na oba jezika."""
        from unittest.mock import patch

        from mujofix.scanners import disk as disk_mod

        class Usage:
            total = 100 * 1024 ** 3
            free = 5 * 1024 ** 3       # 5% -> CRITICAL
            used = total - free

        sc = disk_mod.DiskScanner()
        with patch.object(disk_mod.shutil, "disk_usage", return_value=Usage()):
            bs = sc.scan(ScanContext(lang="bs")).findings[0]
            en = sc.scan(ScanContext(lang="en")).findings[0]
        self.assertEqual(bs.id, "disk-almost-full")
        self.assertIn("gotovo pun", bs.title)
        self.assertIn("5.0 GB", bs.title)
        self.assertIn("almost full", en.title)
        self.assertIn("5.0 GB", en.title)
        for field in FIELDS:
            value = getattr(en, field)
            self.assertFalse(set(BS_CHARS) & set(value.lower()),
                             f"{field}: {value}")


if __name__ == "__main__":
    unittest.main()

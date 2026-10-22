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
MIGRATED = {"config", "disk", "drivers", "duplicates", "network",
            "permissions", "services", "startup", "suspicious"}
# Polja nalaza koja su korisniku vidljiva.
# Prozna polja: moraju ici kroz `self.t(...)`.
FIELDS = ("title", "why", "impact", "risk")
# Tehnicki detalji smiju biti cisti kod (npr. "walk(path)"), pa se
# za njih provjerava samo da ne ostane bosanski tekst s dijakriticima.
TECH_FIELD = "tech_details"


def _hardcoded_fields(source: str) -> list[str]:
    """Polja nalaza koja NISU prevedena preko `self.t(...)`.

    Diakritike nisu dovoljan signal (mnogi bosanski stringovi su ASCII, npr.
    "trazenje programa"), pa se provjerava pravi invariant: svako korisniku
    vidljivo polje mora biti poziv `self.t(...)`.
    """
    bad = []
    for field in FIELDS:
        for line in source.split("\n"):
            stripped = line.strip()
            if not stripped.startswith(f"{field}="):
                continue
            if not stripped.startswith(f"{field}=self.t("):
                bad.append(stripped[:70])
    for line in source.split("\n"):
        stripped = line.strip()
        if stripped.startswith(f"{TECH_FIELD}="):
            if set(BS_CHARS) & set(stripped.lower()):
                bad.append(stripped[:70])
    for match in re.finditer(
            r"def unavailable_reason[^\n]*\n(?:.*\n)*?\s*return\s+(.+)",
            source):
        if "self.t(" not in match.group(1):
            bad.append("unavailable_reason: " + match.group(1)[:50])
    return bad


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

    def test_migrated_scanners_route_all_text_through_self_t(self):
        for name in sorted(MIGRATED):
            source = open(os.path.join(SCANNERS, f"{name}.py"),
                          encoding="utf-8").read()
            leaked = _hardcoded_fields(source)
            self.assertEqual(leaked, [],
                             f"{name}.py ima polja van self.t(...): {leaked}")

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


class TestConsoleEncoding(unittest.TestCase):
    """Windows konzola je pukla na dijakritikama u sazetku (CI smoke)."""

    def test_cli_forces_utf8_and_survives_ascii_only_console(self):
        import io

        from mujofix import cli

        stream = io.TextIOWrapper(io.BytesIO(), encoding="ascii",
                                  errors="strict")
        old_stdout, old_stderr = sys.stdout, sys.stderr
        try:
            sys.stdout = sys.stderr = stream
            cli.force_utf8_console()      # mora prebaciti na utf-8
            print("računar č ć ž š đ")     # prije: UnicodeEncodeError
            sys.stdout.flush()
            written = stream.buffer.getvalue().decode("utf-8")
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr
        self.assertIn("računar", written)

    def test_summarize_is_localized(self):
        from mujofix.cli import summarize

        reports = [{"scanner": "disk", "findings": [{"severity": "LOW"}]}]
        self.assertIn("računar", summarize(reports, "bs"))
        self.assertIn("problems", summarize(reports, "en"))


class TestAllScannersRenderEnglish(unittest.TestCase):
    """Svaki registrovani scanner mora dati engleski tekst kad je lang="en"."""

    def test_every_scanner_is_translated(self):
        from mujofix import cli  # noqa: F401  (registruje scannere)
        from mujofix.scanners.base import REGISTRY, ScanContext

        self.assertTrue(REGISTRY, "nema registrovanih scannera")
        untranslated = []
        for name, cls in sorted(REGISTRY.items()):
            scanner = cls()
            for lang in ("bs", "en"):
                report = scanner.scan(ScanContext(lang=lang))
                texts = [report.skipped or ""]
                for finding in report.findings:
                    texts += [finding.title, finding.why, finding.impact,
                              finding.risk]
                texts = [text for text in texts if text]
                if lang == "en":
                    leaked = [t for t in texts if set(BS_CHARS) & set(t.lower())]
                    if leaked:
                        untranslated.append((name, leaked[:2]))
        self.assertEqual(untranslated, [],
                         f"bosanski tekst u EN izlazu: {untranslated}")

    def test_every_scanner_has_english_skip_reason_on_this_platform(self):
        """"Skipped" razlog mora biti na jeziku gdje god postoji.

        Na Linuxu je vecina scannera preskocena (samo-Windows moduli), na
        Windowsu ih je malo ili nijedan — zato se ne zahtijeva da ih BUDE,
        nego da svaki koji postoji bude na engleskom.
        """
        from mujofix import cli  # noqa: F401  (registruje scannere)
        from mujofix.scanners.base import REGISTRY, ScanContext

        reasons = []
        for name, cls in sorted(REGISTRY.items()):
            report = cls().scan(ScanContext(lang="en"))
            if report.skipped:
                reasons.append((name, report.skipped))
        for name, reason in reasons:
            self.assertFalse(set(BS_CHARS) & set(reason.lower()),
                             f"{name}: {reason}")
            for word in ("samo na Windowsu", "modul nije podrzan", "nije podržan"):
                self.assertNotIn(word, reason, f"{name}: {reason}")


if __name__ == "__main__":
    unittest.main()

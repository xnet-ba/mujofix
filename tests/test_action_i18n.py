"""Cuvar lokalizacije akcija: poruke, opis i rizik moraju biti dvojezicni.

Ratchet: poruke akcija (`return True/False, ...`, `raise RuntimeError(...)`) idu
kroz `ctx.t(...)`, a `description`/`risk` (klasni atributi, bez `ctx`) preko
`action_text(...)`. Za svaku akciju u katalogu mora postojati i bs i en tekst,
i to razlicit (inace je fallback, ne prevod).
"""

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import mujofix.actions.duplicates  # noqa: E402,F401
import mujofix.actions.env  # noqa: E402,F401
import mujofix.actions.hosts  # noqa: E402,F401
import mujofix.actions.power  # noqa: E402,F401
import mujofix.actions.proxy  # noqa: E402,F401
import mujofix.actions.service  # noqa: E402,F401
import mujofix.actions.share  # noqa: E402,F401
import mujofix.actions.startup  # noqa: E402,F401
import mujofix.actions.task  # noqa: E402,F401
import mujofix.actions.temp  # noqa: E402,F401
from mujofix.actions.base import CATALOG, ActionContext, Runner, action_text
from mujofix.i18n.strings import STRINGS

ROOT = os.path.join(os.path.dirname(__file__), "..")
ACTIONS = os.path.join(ROOT, "mujofix", "actions")
BS_CHARS = "čćžšđ"

MESSAGE_RETURN = re.compile(r"^\s*return (?:True|False), (?:f?\"|f?')")
MESSAGE_RAISE = re.compile(r"^\s*raise RuntimeError\((?:f?\"|f?')")


class TestActionText(unittest.TestCase):
    def test_all_actions_have_translated_description_and_risk(self):
        self.assertTrue(CATALOG, "katalog je prazan")
        missing = []
        for name, cls in sorted(CATALOG.items()):
            instance = cls.__new__(cls)  # samo za citanje klasnih atributa
            for field in ("description", "risk"):
                key = f"act_{name}_{field}"
                if key not in STRINGS["bs"] or key not in STRINGS["en"]:
                    missing.append(key)
                    continue
                if action_text(instance, field, "en") == action_text(
                        instance, field, "bs"):
                    missing.append(f"{key} (en == bs)")
        self.assertEqual(missing, [], f"nedostaje prijevod: {missing}")

    def test_no_hardcoded_action_messages(self):
        """Poruke akcija moraju ici kroz ctx.t(...) — bez izuzetka."""
        bad = []
        for name in sorted(os.listdir(ACTIONS)):
            if not name.endswith(".py") or name in ("base.py", "mapping.py"):
                continue
            path = os.path.join(ACTIONS, name)
            for number, line in enumerate(
                    open(path, encoding="utf-8").read().split("\n"), 1):
                if MESSAGE_RETURN.match(line) or MESSAGE_RAISE.match(line):
                    bad.append(f"{name}:{number}: {line.strip()[:60]}")
        self.assertEqual(bad, [], "hardkodovane poruke akcija:\n"
                         + "\n".join(bad))

    def test_english_action_text_has_no_bosnian_diacritics(self):
        bad = [(key, text) for key, text in STRINGS["en"].items()
               if key.startswith("act_") and set(BS_CHARS) & set(text.lower())]
        self.assertEqual(bad, [], f"bosanski znakovi u EN tekstu akcija: {bad}")


class TestActionMessagesRenderLocalized(unittest.TestCase):
    def test_temp_action_messages_in_both_languages(self):
        import tempfile
        import time

        from mujofix.actions.temp import CleanTemp

        with tempfile.TemporaryDirectory() as data:
            path = os.path.join(data, "old.tmp")
            with open(path, "wb") as handle:
                handle.write(b"x")
            old = time.time() - 30 * 86400
            os.utime(path, (old, old))

            bs = ActionContext(quarantine_dir=os.path.join(data, "q"),
                               lang="bs")
            en = ActionContext(quarantine_dir=os.path.join(data, "q2"),
                               lang="en")
            action_bs, action_en = CleanTemp(data), CleanTemp(data)
            self.assertIn("fajlova za karantin",
                          action_bs.precondition(bs)[1])
            self.assertIn("files for quarantine",
                          action_en.precondition(en)[1])

    def test_runner_failure_message_is_localized(self):
        import tempfile

        from mujofix.actions.temp import CleanTemp

        with tempfile.TemporaryDirectory() as data:
            en = ActionContext(quarantine_dir=os.path.join(data, "q"),
                               lang="en")
            result = Runner().run(CleanTemp(os.path.join(data, "nema")), en)
            self.assertIn("precondition failed", result.message)
            self.assertFalse(set(BS_CHARS) & set(result.message.lower()))

    def test_dry_run_message_is_localized(self):
        import tempfile
        import time

        from mujofix.actions.temp import CleanTemp

        with tempfile.TemporaryDirectory() as data:
            path = os.path.join(data, "old.tmp")
            with open(path, "wb") as handle:
                handle.write(b"x")
            old = time.time() - 30 * 86400
            os.utime(path, (old, old))
            en = ActionContext(quarantine_dir=os.path.join(data, "q"),
                               lang="en", dry_run=True)
            result = Runner().run(CleanTemp(data), en)
            self.assertIn("dry-run, nothing was changed", result.message)


if __name__ == "__main__":
    unittest.main()

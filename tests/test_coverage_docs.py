"""Cuvar tabele pokrivenosti popravkama u README-u (bs+en).

Tabela je izmedju markera `<!-- coverage:start/end -->` i mora se poklapati sa
KODOM: skup id-jeva nalaza dolazi iz scannera, a ✅/❌ iz `mapping.py`. Ako se
doda nalaz ili akcija bez azuriranja README-a, ovaj test pada.
"""

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

ROOT = os.path.join(os.path.dirname(__file__), "..")
SCANNERS = os.path.join(ROOT, "mujofix", "scanners")
MAPPING = os.path.join(ROOT, "mujofix", "actions", "mapping.py")
BLOCK = re.compile(r"<!-- coverage:start -->(.*?)<!-- coverage:end -->", re.S)
ROW = re.compile(r"^\|\s*`([a-z0-9\-]+)`\s*\|\s*(✅|❌)", re.M)


def finding_ids() -> set[str]:
    ids: set[str] = set()
    for name in sorted(os.listdir(SCANNERS)):
        if not name.endswith(".py") or name == "base.py":
            continue
        source = open(os.path.join(SCANNERS, name), encoding="utf-8").read()
        ids |= set(re.findall(r'id="([a-z0-9\-]+)"', source))
    return ids


def handled_ids() -> set[str]:
    source = open(MAPPING, encoding="utf-8").read()
    return set(re.findall(r'fid == "([a-z0-9\-]+)"', source))


def readme_rows(path: str) -> dict[str, str]:
    text = open(path, encoding="utf-8").read()
    match = BLOCK.search(text)
    assert match, f"{path}: nema coverage bloka"
    return {fid: mark for fid, mark in ROW.findall(match.group(1))}


class TestCoverageTable(unittest.TestCase):
    def setUp(self):
        self.ids = finding_ids()
        self.handled = handled_ids()
        self.assertTrue(self.ids, "nema id-jeva nalaza")

    def test_table_lists_exactly_the_findings_from_code(self):
        for readme in ("README.md", "README.en.md"):
            rows = readme_rows(os.path.join(ROOT, readme))
            self.assertEqual(set(rows), self.ids,
                             f"{readme}: tabela se ne poklapa sa kodom")

    def test_marks_match_the_mapping(self):
        for readme in ("README.md", "README.en.md"):
            rows = readme_rows(os.path.join(ROOT, readme))
            for fid, mark in rows.items():
                expected = "✅" if fid in self.handled else "❌"
                self.assertEqual(mark, expected,
                                 f"{readme}: {fid} ima {mark}, kod kaze {expected}")

    def test_header_count_matches(self):
        for readme in ("README.md", "README.en.md"):
            text = open(os.path.join(ROOT, readme), encoding="utf-8").read()
            block = BLOCK.search(text).group(1)
            numbers = [int(n) for n in re.findall(r"<b>(\d+)", block)]
            self.assertEqual(numbers, [len(self.ids), len(self.handled)],
                             f"{readme}: brojevi u uvodu tabele ne odgovaraju")


if __name__ == "__main__":
    unittest.main()

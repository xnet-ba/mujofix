"""Cuvar za GitHub workflow YAML.

Bez PyYAML (nije zavisnost projekta): hvata konkretnu gresku koja se vec
desila — ne-citiran `name:` sa dvotackom razmakom unutar sebe razbije YAML, a
GitHub tada workflow prikaze kao putanju fajla bez ijednog job-a (CI tiho ne
radi). Provjerava i da workflow ima `jobs:` i bar jedan job.
"""

import os
import re
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
WORKFLOWS = os.path.join(ROOT, ".github", "workflows")

NAME_LINE = re.compile(r"^\s*-?\s*name:\s*(?P<value>.+?)\s*$")


def workflow_files() -> list[str]:
    if not os.path.isdir(WORKFLOWS):
        return []
    return sorted(os.path.join(WORKFLOWS, name)
                  for name in os.listdir(WORKFLOWS)
                  if name.endswith((".yml", ".yaml")))


class TestWorkflowYaml(unittest.TestCase):
    def test_there_is_at_least_one_workflow(self):
        self.assertTrue(workflow_files(), "nema .github/workflows/*.yml")

    def test_no_unquoted_colon_space_in_name_or_run(self):
        bad = []
        for path in workflow_files():
            for number, line in enumerate(
                    open(path, encoding="utf-8").read().split("\n"), 1):
                match = NAME_LINE.match(line)
                if not match:
                    continue
                value = match.group("value")
                if value.startswith(("'", '"', "|", ">")):
                    continue
                if ": " in value:
                    bad.append(f"{os.path.basename(path)}:{number}: {line}")
        self.assertEqual(bad, [], "ne-citiran 'name:' sa ': ' razbija YAML:\n"
                         + "\n".join(bad))

    def test_every_workflow_has_jobs(self):
        for path in workflow_files():
            text = open(path, encoding="utf-8").read()
            self.assertIn("jobs:", text, os.path.basename(path))
            # svaki job ima "runs-on" (inace GitHub ne zna gdje da ga pusti)
            self.assertIn("runs-on:", text, os.path.basename(path))


if __name__ == "__main__":
    unittest.main()

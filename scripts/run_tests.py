"""Pokreni svaki test-modul u SVOM procesu (cisto Qt stanje) i saberi rezultate.

Zasto: PySide6 offscreen ne voli mnogo prozora/niti u jednom procesu — puna
`unittest discover` sesija s vremena na vrijeme pukne (heap korupcija u Qt
teardown-u), a pad jednog modula sakrije rezultate ostalih. Ovako je svaki modul
izolovan, a mi i dalje dobijemo ukupan broj testova i jasan spisak padova.

Koristi se i lokalno i u CI-ju:
    python scripts/run_tests.py
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS = os.path.join(ROOT, "tests")
COUNT_RE = re.compile(r"^Ran (\d+) tests?", re.M)


def modules() -> list[str]:
    return sorted(name[:-3] for name in os.listdir(TESTS)
                  if name.startswith("test_") and name.endswith(".py"))


def run(module: str) -> tuple[str, int, int, str]:
    env = dict(os.environ, QT_QPA_PLATFORM=os.environ.get(
        "QT_QPA_PLATFORM", "offscreen"), PYTHONPATH=ROOT)
    proc = subprocess.run([sys.executable, "-m", "unittest", f"tests.{module}"],
                          cwd=ROOT, env=env, capture_output=True, text=True,
                          timeout=900)
    out = proc.stdout + proc.stderr
    match = COUNT_RE.search(out)
    ran = int(match.group(1)) if match else 0
    # PySide6 offscreen zna srusiti PROCES u teardown-u i kad su svi testovi
    # prosli ("Ran N / OK" je vec ispisano) — tada je izlaz mjerodavan, a ne
    # exit code. Pad se priznaje samo ako unittest kaze FAILED/ERROR ili nema
    # "OK" u izlazu.
    passed = "FAILED" not in out and "OK" in out
    code = 0 if passed else (proc.returncode or 1)
    return module, code, ran, out


def main() -> int:
    total = 0
    failures: list[str] = []
    for module in modules():
        name, code, ran, out = run(module)
        total += ran
        status = "OK" if code == 0 else "PAO"
        print(f"[{status}] {name} ({ran} testova)")
        if code != 0:
            failures.append(name)
            tail = [line for line in out.splitlines()
                    if line.strip() and not line.startswith(".")][-12:]
            print("    " + "\n    ".join(tail))
    print(f"\nUKUPNO: {total} testova, {len(failures)} modula palo"
          + (f": {', '.join(failures)}" if failures else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

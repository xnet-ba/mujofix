"""MujoFix CLI: engine se mora moci pokretati i iz CLI-ja (testiranje).

Koristenje:
  python -m mujofix.cli scan [--scanner startup|disk|services] [--summary]
Bez --summary ispisuje masinski JSON; uz --summary kratak tekst obicnim jezikom.
"""

from __future__ import annotations

import argparse
import json
import platform as std_platform
import sys

sys.path.insert(0, __import__("os").path.join(
    __import__("os").path.dirname(__file__), "..", ".."))

from mujofix.scanners import base as _base  # noqa: E402,F401  (registracija)
from mujofix.scanners import config as _config  # noqa: E402,F401
from mujofix.scanners import disk as _disk  # noqa: E402,F401
from mujofix.scanners import drivers as _drivers  # noqa: E402,F401
from mujofix.scanners import duplicates as _duplicates  # noqa: E402,F401
from mujofix.scanners import network as _network  # noqa: E402,F401
from mujofix.scanners import permissions as _permissions  # noqa: E402,F401
from mujofix.scanners import services as _services  # noqa: E402,F401
from mujofix.scanners import suspicious as _suspicious  # noqa: E402,F401
from mujofix.scanners import startup as _startup  # noqa: E402,F401
from mujofix.scanners.base import REGISTRY, ScanContext  # noqa: E402


def run_scan(names: list[str] | None) -> list[dict]:
    ctx = ScanContext()
    selected = names or sorted(REGISTRY)
    reports = []
    for name in selected:
        cls = REGISTRY.get(name)
        if cls is None:
            reports.append({"scanner": name, "findings": [],
                            "skipped": f"nepoznat scanner '{name}'"})
            continue
        report = cls().scan(ctx)
        reports.append({
            "scanner": report.scanner,
            "duration_s": round(report.duration_s, 2),
            "skipped": report.skipped,
            "findings": [f.to_dict() for f in report.findings],
        })
    return reports


def summarize(reports: list[dict]) -> str:
    counts = {"CRITICAL": 0, "MEDIUM": 0, "LOW": 0}
    for report in reports:
        for finding in report["findings"]:
            counts[finding["severity"]] += 1
    total = sum(counts.values())
    return (f"Tvoj racunar ima {total} problema.\n"
            f"  {counts['CRITICAL']} ozbiljna  "
            f"{counts['MEDIUM']} srednja  "
            f"{counts['LOW']} mala")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mujofix", description="MujoFix engine CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)
    scan = sub.add_parser("scan", help="pokreni scannere")
    scan.add_argument("--scanner", action="append", default=None)
    scan.add_argument("--summary", action="store_true")
    scan.add_argument("--out", default=None,
                      help="upisi nalaze za MCP server "
                           "(mujofix_mcp.py --findings <fajl>)")
    args = parser.parse_args(argv)
    reports = run_scan(args.scanner)
    if args.out:
        findings = [f for r in reports for f in r["findings"]
                    if not r["skipped"]]
        payload = {"findings": findings,
                   "system_info": {"os": std_platform.system(),
                                   "release": std_platform.release()}}
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
    if args.summary:
        print(summarize(reports))
    else:
        print(json.dumps(reports, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

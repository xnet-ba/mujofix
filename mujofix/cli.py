"""MujoFix CLI: engine se mora moci pokretati i iz CLI-ja (testiranje).

Koristenje:
  python -m mujofix.cli scan [--scanner startup|disk|services] [--summary]
Bez --summary ispisuje masinski JSON; uz --summary kratak tekst obicnim jezikom.
"""

from __future__ import annotations

import argparse
import json
import os
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
from mujofix import update as update_mod  # noqa: E402


def force_utf8_console() -> None:
    """Prebaci stdout/stderr na UTF-8 — Windows konzola inace puca na "č/š/ž".

    Nas tekst je dvojezican i sadrzi dijakritike; legacy code page (cp437/
    cp1252) baca UnicodeEncodeError pri `print` (dokazano u CI smoke koraku).
    `errors="replace"` znaci da se ne moze srusiti cak i ako terminal ne
    podrzava znak.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def run_scan(names: list[str] | None, lang: str = "bs") -> list[dict]:
    ctx = ScanContext(lang=lang)
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


def summarize(reports: list[dict], lang: str = "bs") -> str:
    """Sazetak skeniranja na jeziku `lang` (isti izvor stringova kao GUI)."""
    from mujofix.i18n.strings import tr

    counts = {"CRITICAL": 0, "MEDIUM": 0, "LOW": 0}
    for report in reports:
        for finding in report["findings"]:
            counts[finding["severity"]] += 1
    return tr("cli_summary", lang, n=sum(counts.values()),
              c=counts["CRITICAL"], m=counts["MEDIUM"], l=counts["LOW"])


def _cmd_update(args) -> int:
    try:
        info = update_mod.check_for_update(api_url=args.api)
    except update_mod.UpdateError as exc:
        print(f"Provjera update-a nije uspjela: {exc}")
        return 1
    if not info["available"]:
        print(f"Verzija {info['current']} je najnovija.")
        return 0
    print(f"Nova verzija: {info['latest']} (imam {info['current']}).")
    if not args.apply:
        return 0
    try:
        result = update_mod.apply_update(info)
    except update_mod.UpdateError as exc:
        print(f"Update nije uspio: {exc}")
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    force_utf8_console()
    parser = argparse.ArgumentParser(prog="mujofix", description="MujoFix engine CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)
    scan = sub.add_parser("scan", help="pokreni scannere")
    scan.add_argument("--scanner", action="append", default=None)
    scan.add_argument("--summary", action="store_true")
    scan.add_argument("--lang", default="bs", choices=("bs", "en"),
                      help="jezik teksta nalaza (bs|en)")
    scan.add_argument("--out", default=None,
                      help="upisi nalaze za MCP server "
                           "(mujofix_mcp.py --findings <fajl>)")
    upd = sub.add_parser("update", help="provjeri ima li nova verzija")
    upd.add_argument("--apply", action="store_true",
                     help="preuzmi, provjeri sha256 i pokreni (Windows)")
    upd.add_argument("--api", default=update_mod.RELEASES_API)
    # stdio MCP server koji opencode spawn-uje kao svoj alat (vidi agent_config).
    mcp = sub.add_parser("mcp", help="MujoFix MCP server (stdio, samo za AI)")
    mcp.add_argument("--findings", default=os.environ.get("MUJOFIX_FINDINGS"),
                     help="JSON izlaz scannera (default: $MUJOFIX_FINDINGS)")
    args = parser.parse_args(argv)

    if args.cmd == "mcp":
        from mujofix.ai.mujofix_mcp import load_findings_file, serve
        if args.findings:
            load_findings_file(args.findings)
        serve()
        return 0

    if args.cmd == "update":
        return _cmd_update(args)

    reports = run_scan(args.scanner, lang=getattr(args, 'lang', 'bs'))
    if args.out:
        findings = [f for r in reports for f in r["findings"]
                    if not r["skipped"]]
        payload = {"findings": findings,
                   "system_info": {"os": std_platform.system(),
                                   "release": std_platform.release()}}
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
    if args.summary:
        print(summarize(reports, lang=getattr(args, 'lang', 'bs')))
    else:
        print(json.dumps(reports, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

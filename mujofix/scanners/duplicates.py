"""Duplikati: velicina -> djelimicni hash (64 KB) -> puni sha256.

Fajlovi veci od 2 GB se ne hasiraju cijeli (granica); slazu se po velicini +
parcijalnom hashu i prijavljuju kao "vjerovatno duplikat" (nesigurnost je
izricita). Sistemski folderi se preskacu. Duplikati se NIKAD ne brisu
automatski: reversible=False, bez akcijske mape.
"""

from __future__ import annotations

import hashlib
import os

from mujofix.core.models import Finding
from mujofix.scanners.base import ScanContext, Scanner, register

MIN_SIZE_BYTES = 10 * 1024**2
PARTIAL_BYTES = 64 * 1024
FULL_HASH_CAP_BYTES = 2 * 1024**3
WALK_CAP_FILES = 200_000

EXCLUDE_DIRS = {
    "windows", "program files", "program files (x86)", "programdata",
    "$recycle.bin", "system volume information", "appdata",
    ".git", "node_modules", "__pycache__", ".venv", "venv",
}


def _default_roots() -> list[str]:
    home = os.path.expanduser("~")
    return [home] if os.path.isdir(home) else []


def _safe_size(path: str) -> int:
    try:
        return os.path.getsize(path)
    except OSError:
        return -1


def _hash_prefix(path: str) -> str | None:
    try:
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            digest.update(handle.read(PARTIAL_BYTES))
        return digest.hexdigest()
    except OSError:
        return None


def _hash_full(path: str) -> str | None:
    try:
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(8 * 1024**2), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


@register
class DuplicatesScanner(Scanner):
    name = "duplicates"

    def __init__(self, roots: list[str] | None = None):
        self.roots = roots if roots is not None else _default_roots()

    def _scan(self, ctx: ScanContext) -> list[Finding]:
        by_size: dict[int, list[str]] = {}
        walked = 0
        for root in self.roots:
            for dirpath, dirnames, filenames in os.walk(root):
                if ctx.cancelled:
                    return []
                dirnames[:] = [d for d in dirnames
                               if d.lower() not in EXCLUDE_DIRS]
                for name in filenames:
                    path = os.path.join(dirpath, name)
                    size = _safe_size(path)
                    if size >= MIN_SIZE_BYTES:
                        by_size.setdefault(size, []).append(path)
                    walked += 1
                    if walked >= WALK_CAP_FILES:
                        break
                if walked >= WALK_CAP_FILES:
                    break
        groups: list[dict] = []
        for size, paths in by_size.items():
            if len(paths) < 2 or ctx.cancelled:
                continue
            by_partial: dict[str, list[str]] = {}
            for path in paths:
                digest = _hash_prefix(path)
                if digest:
                    by_partial.setdefault(digest, []).append(path)
            for candidates in by_partial.values():
                if len(candidates) < 2:
                    continue
                small = [p for p in candidates
                         if _safe_size(p) <= FULL_HASH_CAP_BYTES]
                big = [p for p in candidates
                       if _safe_size(p) > FULL_HASH_CAP_BYTES]
                if len(small) >= 2:
                    by_full: dict[str, list[str]] = {}
                    for path in small:
                        digest = _hash_full(path)
                        if digest:
                            by_full.setdefault(digest, []).append(path)
                    for confirmed in by_full.values():
                        if len(confirmed) >= 2:
                            groups.append({"certain": True, "size": size,
                                           "paths": sorted(confirmed)})
                if len(big) >= 2:
                    groups.append({"certain": False, "size": size,
                                   "paths": sorted(big),
                                   "note": "samo velicina+64KB (fajl >2GB)"})
        if not groups:
            return []
        wasted = sum(g["size"] * (len(g["paths"]) - 1) for g in groups)
        return [Finding(
            id="duplicates-found", scanner=self.name,
            title=(f"{len(groups)} grupa duplikata "
                   f"(~{wasted // 1024**2} MB viška)"),
            why="Iste velike datoteke na vise mjesta jedu disk. Brisanje je "
                "rucno — aplikacija nista ne brise automatski.",
            severity="MEDIUM" if wasted >= 1024**3 else "LOW",
            impact=f"moguce oslobadjanje ~{wasted // 1024**2} MB (rucno)",
            risk="nema: samo pregled, bez akcije",
            reversible=False,
            evidence={"groups": groups[:20],
                      "wasted_bytes": wasted, "walked_files": walked},
            tech_details="velicina -> sha256(64KB) -> puni sha256",
        )]

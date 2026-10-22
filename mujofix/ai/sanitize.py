"""Anonimizacija prije slanja AI-ju: korisnicko ime, hostname, IP/MAC,
serijski brojevi, putanje do licnih fajlova. Nikad sadrzaj fajlova, lozinke,
tokeni ni registry vrijednosti s tajnama (takvi kljucevi se dropaju cijeli).
"""

from __future__ import annotations

import re

RE_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
RE_MAC = re.compile(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b")
# Serijski brojevi dolaze i malim slovima (npr. "abcde-1234"), pa je regex
# case-insensitive, ali MORA sadrzavati cifru — inace bi pojeo obican tekst
# poput "windows-update" (bez cifre) i oslabio objasnjenje.
RE_SERIAL = re.compile(r"\b(?=[A-Za-z0-9-]*\d)[A-Za-z0-9]{5,}-[A-Za-z0-9-]{4,}\b")

DROP_KEYS = {"password", "passwd", "token", "secret", "api_key", "apikey",
             "auth", "credential"}

# Tokeni mogu biti i u VRIJEDNOSTI (npr. u slobodnom tekstu nalaza), pa se
# skidaju i po obliku. Namjerno usko: samo poznati prefiksi, da se ne pojede
# obican tekst.
RE_TOKEN = re.compile(
    r"(?:ghp_|gho_|ghu_|ghs_|github_pat_)[A-Za-z0-9_]{10,}"
    r"|sk-[A-Za-z0-9]{16,}"
    r"|xox[baprs]-[A-Za-z0-9-]{10,}"
    r"|AKIA[0-9A-Z]{16}"
    r"|Bearer\s+[A-Za-z0-9._-]{16,}"
)


def _scrub_str(text: str, username: str, hostname: str) -> str:
    if username:
        text = re.sub(re.escape(username), "<korisnik>", text,
                      flags=re.IGNORECASE)
        text = re.sub(r"C:\\Users\\[^\\]+", r"C:\\Users\\<korisnik>", text)
        text = re.sub(r"/(home|Users)/[^/]+", r"/\1/<korisnik>", text)
    if hostname:
        text = re.sub(re.escape(hostname), "<racunar>", text,
                      flags=re.IGNORECASE)
    text = RE_TOKEN.sub("<token>", text)
    text = RE_IPV4.sub("<ip>", text)
    text = RE_MAC.sub("<mac>", text)
    text = RE_SERIAL.sub("<serijski>", text)
    return text


def sanitize(obj, username: str = "", hostname: str = ""):
    """Rekurzivno ocisti dict/list/str. Cista funkcija, bez mreze."""
    if isinstance(obj, str):
        return _scrub_str(obj, username, hostname)
    if isinstance(obj, dict):
        return {k: ("<uklonjeno>" if k.lower() in DROP_KEYS
                    else sanitize(v, username, hostname))
                for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v, username, hostname) for v in obj]
    return obj

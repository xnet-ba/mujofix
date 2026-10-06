"""Anonimizacija prije slanja AI-ju: korisnicko ime, hostname, IP/MAC,
serijski brojevi, putanje do licnih fajlova. Nikad sadrzaj fajlova, lozinke,
tokeni ni registry vrijednosti s tajnama (takvi kljucevi se dropaju cijeli).
"""

from __future__ import annotations

import re

RE_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
RE_MAC = re.compile(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b")
RE_SERIAL = re.compile(r"\b[A-Z0-9]{5,}-[A-Z0-9-]{4,}\b")

DROP_KEYS = {"password", "passwd", "token", "secret", "api_key", "apikey",
             "auth", "credential"}


def _scrub_str(text: str, username: str, hostname: str) -> str:
    if username:
        text = re.sub(re.escape(username), "<korisnik>", text,
                      flags=re.IGNORECASE)
        text = re.sub(r"C:\\Users\\[^\\]+", r"C:\\Users\\<korisnik>", text)
        text = re.sub(r"/(home|Users)/[^/]+", r"/\1/<korisnik>", text)
    if hostname:
        text = re.sub(re.escape(hostname), "<racunar>", text,
                      flags=re.IGNORECASE)
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

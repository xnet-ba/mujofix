"""Auto-update: provjeri GitHub Releases, preuzmi, provjeri sha256, pokreni.

Qt-free da se testira bez PySide6. Mrezni put i pokretanje preuzetog artefakta
su NETESTIRANI (bez Win VM-a); sve ostalo je pokriveno unit testovima s
ubacenim (fake) fetch/download funkcijama.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import urllib.request

from mujofix.platform.windows import NotSupported, is_windows
from mujofix.version import current_version

RELEASES_API = "https://api.github.com/repos/xnet-ba/mujofix/releases/latest"
SUMS_NAME = "SHA256SUMS.txt"
_USER_AGENT = "MujoFix-updater"


def _t(key: str, lang: str = "bs", **fmt: object) -> str:
    """Lokalizovana poruka (update greske korisnik vidi u GUI-ju i CLI-ju)."""
    from mujofix.i18n.strings import tr

    return tr(key, lang, **fmt)


class UpdateError(Exception):
    """Provjera/preuzimanje/verifikacija update-a nije uspjela."""


def _parse_version(text: str, lang: str = "bs") -> tuple[int, int, int]:
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", text or "")
    if not match:
        raise UpdateError(_t("up_bad_version", lang, v=text))
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def is_newer(latest: str, current: str, lang: str = "bs") -> bool:
    """Je li 'latest' (npr. 'v0.2.0') strogo novija od 'current'."""
    return _parse_version(latest) > _parse_version(current)


def fetch_latest(api_url: str = RELEASES_API, timeout: int = 10,
                 lang: str = "bs") -> dict:
    """GitHub 'releases/latest' -> {tag, assets:[{name,url,size}]}."""
    req = urllib.request.Request(
        api_url, headers={"Accept": "application/vnd.github+json",
                          "User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.load(resp)
    except Exception as exc:
        raise UpdateError(_t("up_unreachable", lang, u=api_url, e=exc)) from exc
    return {
        "tag": data.get("tag_name", ""),
        "assets": [
            {"name": a.get("name", ""), "url": a.get("browser_download_url", ""),
             "size": a.get("size", 0)}
            for a in data.get("assets", [])
        ],
    }


def find_asset(assets: list[dict], name: str) -> dict | None:
    lowered = name.lower()
    for asset in assets:
        if asset["name"].lower() == lowered:
            return asset
    return None


def pick_asset(assets: list[dict],
               suffixes: tuple[str, ...] = (".exe", ".msi", ".zip")) -> dict | None:
    """Preferiraj installer (.exe/.msi), inace arhivu (.zip). Nikad SHA256SUMS."""
    for suffix in suffixes:
        for asset in assets:
            name = asset["name"].lower()
            if name.endswith(suffix) and SUMS_NAME.lower() not in name:
                return asset
    return None


def parse_sha256sums(text: str) -> dict[str, str]:
    """'<hash>  <ime>' (ili '*<ime>') -> {ime: hash}."""
    sums: dict[str, str] = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 2 and re.fullmatch(r"[0-9a-fA-F]{64}", parts[0]):
            sums[parts[1].lstrip("*")] = parts[0].lower()
    return sums


def fetch_text(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def download(url: str, dest: str, expected_sha256: str | None = None,
             lang: str = "bs",
             timeout: int = 60) -> str:
    """Preuzmi url u dest; ako je zadan hash, provjeri i odbaci na neslaganje."""
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    digest = hashlib.sha256()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            with open(dest, "wb") as out:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    out.write(chunk)
                    digest.update(chunk)
    except Exception as exc:
        raise UpdateError(_t("up_download_failed", lang, e=exc)) from exc
    if expected_sha256 and digest.hexdigest().lower() != expected_sha256.lower():
        os.remove(dest)
        raise UpdateError(_t("up_sha_mismatch", lang))
    return dest


def launch_artifact(path: str) -> bool:
    """Pokreni preuzeti artefakt (installer) ili otvori folder. Samo Windows."""
    if not is_windows():
        raise NotSupported("pokretanje preuzetog fajla postoji samo na Windowsu")
    os.startfile(path)  # noqa: S606 - namjerno pokrecemo preuzeti (verifikovani) fajl
    return True


def check_for_update(current: str | None = None, api_url: str = RELEASES_API,
                     fetch=fetch_latest, lang: str = "bs") -> dict:
    """Vrati {available, current, latest, tag, asset, assets}."""
    current = current or current_version()
    # injektovani `fetch` (testovi) drzi stari ugovor; nas default prima jezik
    release = (fetch(api_url, lang=lang) if fetch is fetch_latest
               else fetch(api_url))
    assets = release.get("assets", [])
    tag = release.get("tag", "")
    available = bool(tag) and is_newer(tag, current, lang)
    return {
        "available": available,
        "current": current,
        "latest": tag.lstrip("v"),
        "tag": tag,
        "asset": pick_asset(assets) if available else None,
        "assets": assets,
    }


def apply_update(info: dict, workdir: str | None = None, lang: str = "bs",
                 download_fn=download, launch_fn=launch_artifact,
                 fetch_text_fn=fetch_text) -> dict:
    """Preuzmi izabrani artefakt (uz sha256 kad je SHA256SUMS dostupan) i pokreni."""
    asset = info.get("asset")
    if not asset:
        raise UpdateError(_t("up_no_asset", lang))
    expected = None
    sums = find_asset(info.get("assets", []), SUMS_NAME)
    if sums:
        try:
            expected = parse_sha256sums(fetch_text_fn(sums["url"])).get(asset["name"])
        except Exception:
            expected = None  # bez sums-a: preuzimamo bez verifikacije
    workdir = workdir or tempfile.mkdtemp(prefix="mujofix-upd-")
    dest = os.path.join(workdir, asset["name"])
    if download_fn is download:
        download_fn(asset["url"], dest, expected, lang=lang)
    else:  # injektovano u testovima
        download_fn(asset["url"], dest, expected)
    return {"path": dest, "launched": launch_fn(dest), "sha256": expected}

"""Verzija aplikacije: jedan izvor istine je CHANGELOG.md (vrh, "## [x.y.z]").

CHANGELOG.md se bundluje u build (vidi mujofix.spec) pa i zamrznuta aplikacija
cita istu verziju. Ako fajl nije dostupan, pada na konstantu (netestirano u
frozen exe-u bez CHANGELOG-a).
"""

from __future__ import annotations

import os
import re

_FALLBACK = "0.3.0"
_CHANGELOG = os.path.join(os.path.dirname(__file__), "..", "CHANGELOG.md")


def current_version() -> str:
    """Verzija iz CHANGELOG.md ili fallback konstanta."""
    try:
        with open(_CHANGELOG, encoding="utf-8") as handle:
            match = re.search(r"## \[(\d+\.\d+\.\d+)\]", handle.read())
        if match:
            return match.group(1)
    except OSError:
        pass
    return _FALLBACK

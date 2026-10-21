"""Bundlovani OpenCode kao CLI child proces (bez servera i bez web UI-a).

MujoFix NEMA lokalni backend: nema `opencode serve`, nema HTTP porta, nema
lozinke i nista se ne izlaze na mrezu. Objasnjenje se dobija pokretanjem
`opencode run` kao child procesa (vidi `ai/provider.py`), koji nas agent i
MCP alate cita iz izolovanog `opencode.json` (vidi `ai/agent_config.py`).

Bezbjednosni ugovor (pokriven testovima):
- nikad se ne prosljedjuje --dangerously-skip-permissions / --auto /
  --share / --mdns
- dijete se pokrece sa izolovanim XDG_CONFIG_HOME (nas config se ne stapa sa
  korisnickim globalnim)

Provjereno uz pinovani opencode 1.18.34/1.18.35: `opencode run` radi bez
`--attach` (CLI sam vodi poziv modela), a `opencode debug config` sa
izolovanim config-home vidi nas agent sa svih 11 alata `deny` + `mcp_*`.
"""

from __future__ import annotations

import os
import shutil

FORBIDDEN_FLAGS = (
    "--dangerously-skip-permissions",
    "--auto",
    "--share",
    "--mdns",
    # server/HTTP forma: MujoFix je desktop app, ne web UI na lokalnom backendu
    "--attach",
    "--port",
    "--hostname",
)


class OpencodeNotFound(FileNotFoundError):
    """Bundlovani OpenCode binary nije pronadjen."""


def bundled_binary() -> str:
    """Vrati putanju do OpenCode binarnog fajla (samo stdlib, bez Node-a)."""
    candidates: list[str] = []
    override = os.environ.get("MUJOFIX_OPENCODE_BIN")
    if override:
        candidates.append(override)
    localappdata = os.environ.get("LOCALAPPDATA", "")
    if localappdata:
        candidates.append(
            os.path.join(localappdata, "MujoFix", "opencode", "opencode.exe")
        )
    found = shutil.which("opencode")
    if found:
        candidates.append(found)
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate
    raise OpencodeNotFound(
        "OpenCode binary nije pronadjen. Postavi MUJOFIX_OPENCODE_BIN ili "
        "instaliraj bundlovanu kopiju u %LOCALAPPDATA%\\MujoFix\\opencode\\."
    )

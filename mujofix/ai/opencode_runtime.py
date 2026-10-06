"""Pokretanje bundlovanog OpenCode servera kao child procesa (Faza 0 SPIKE).

Bezbjednosni ugovor (pokriven testovima u tests/test_phase0_spike.py):
- slusa SAMO na 127.0.0.1, port biramo mi (slobodan), nikad 0.0.0.0
- basic auth sa lozinkom generisanom po pokretanju (OPENCODE_SERVER_PASSWORD)
- nigdje se ne prosljedjuje --dangerously-skip-permissions / --auto /
  --share / --mdns
- close() uvijek gasi child proces (terminate -> kill); nema zaostalih procesa

Provjereno uz: opencode 1.18.34 (`serve`, default hostname 127.0.0.1),
docs https://opencode.ai/docs/server/.
Izolacija config/data direktorija pinovane verzije: NETESTIRANO (Faza 0, tacka 1).
"""

from __future__ import annotations

import base64
import os
import secrets
import shutil
import socket
import subprocess
import time
import urllib.request

FORBIDDEN_FLAGS = (
    "--dangerously-skip-permissions",
    "--auto",
    "--share",
    "--mdns",
)

_HEALTH_PATH = "/doc"
_START_TIMEOUT_S = 30.0


class OpencodeNotFound(FileNotFoundError):
    """Bundlovani OpenCode binary nije pronadjen."""


class OpencodeNotHealthy(RuntimeError):
    """Server se nije javio na health check u roku."""


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


def pick_free_port() -> int:
    """Slobodan port na 127.0.0.1 (mali race prozor, prihvatljivo za spike)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class OpencodeServer:
    """`opencode serve` child proces: 127.0.0.1 + slucajan port + slucajna lozinka."""

    def __init__(
        self,
        binary: str,
        workdir: str,
        extra_env: dict[str, str] | None = None,
        timeout_s: float = _START_TIMEOUT_S,
    ) -> None:
        self.binary = binary
        self.workdir = workdir
        self.extra_env = dict(extra_env or {})
        self.timeout_s = timeout_s
        self.port = pick_free_port()
        self.password = secrets.token_urlsafe(32)
        self.username = "opencode"
        self._proc: subprocess.Popen[bytes] | None = None

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def _cmd(self) -> list[str]:
        cmd = [
            self.binary,
            "serve",
            "--hostname",
            "127.0.0.1",
            "--port",
            str(self.port),
        ]
        for flag in FORBIDDEN_FLAGS:
            assert flag not in cmd, f"zabranjen flag u komandi: {flag}"
        return cmd

    def _auth_header(self) -> dict[str, str]:
        token = base64.b64encode(
            f"{self.username}:{self.password}".encode()
        ).decode()
        return {"Authorization": f"Basic {token}"}

    def _healthy(self, with_auth: bool) -> bool:
        req = urllib.request.Request(
            self.url + _HEALTH_PATH,
            headers=self._auth_header() if with_auth else {},
        )
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    def start(self) -> "OpencodeServer":
        env = dict(os.environ)
        env["OPENCODE_SERVER_PASSWORD"] = self.password
        env["OPENCODE_SERVER_USERNAME"] = self.username
        env.update(self.extra_env)
        # ponytail: global lock nije potreban, jedan server po pokretanju
        self._proc = subprocess.Popen(
            self._cmd(),
            cwd=self.workdir,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.time() + self.timeout_s
        while time.time() < deadline:
            if self._proc.poll() is not None:
                raise OpencodeNotHealthy(
                    f"opencode serve se ugasio pri startu (exit={self._proc.poll()})"
                )
            if self._healthy(with_auth=True):
                return self
            time.sleep(0.3)
        self.close()
        raise OpencodeNotHealthy(
            f"server se nije javio na {self.url}{_HEALTH_PATH} "
            f"za {self.timeout_s}s"
        )

    def requires_auth(self) -> bool:
        """True ako endpoint bez lozinke ne prolazi (ocekivano: True)."""
        return not self._healthy(with_auth=False)

    def close(self) -> None:
        proc, self._proc = self._proc, None
        if proc is None or proc.poll() is not None:
            return
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)

    def __enter__(self) -> "OpencodeServer":
        return self.start()

    def __exit__(self, *exc: object) -> None:
        self.close()

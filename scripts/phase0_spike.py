"""Faza 0 SPIKE: 5 provjera na (po mogucnosti cistom) Windows VM-u.

Koristenje (PowerShell):
  python scripts/phase0_spike.py [--model provider/model] [--binary putanja]

Svaka provjera ispisuje PASS / SKIP / FAIL. Exit kod 0 samo ako nema FAIL.
SKIP znaci "nije se moglo provjeriti u ovom okruzenju" (npr. nema model
kredencijala) i ne lazno prolazi.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mujofix.ai.agent_config import (
    AGENT_ID,
    offline_explain,
    write_config,
)
from mujofix.ai.mujofix_mcp import SPIKE_MARKER
from mujofix.ai.opencode_runtime import (
    OpencodeNotFound,
    OpencodeNotHealthy,
    OpencodeServer,
    bundled_binary,
)

# Heuristika: ovi tragovi u stderr znace "nema modela/kredencijala", ne bug.
NO_MODEL_HINTS = (
    "auth",
    "login",
    "provider",
    "api key",
    "apikey",
    "401",
    "402",
    "quota",
    "credit",
    "model",
    "zen",
)

Result = tuple[str, str]  # (status, poruka)


def check_1_binary() -> tuple[str, str, str]:
    """1. Bundlovani binary se pokrece bez Node-a."""
    try:
        binary = bundled_binary()
    except OpencodeNotFound as exc:
        return "FAIL", "", str(exc)
    proc = subprocess.run(
        [binary, "--version"], capture_output=True, text=True, timeout=30
    )
    if proc.returncode != 0:
        return "FAIL", binary, "`--version` nije uspio"
    return "PASS", binary, proc.stdout.strip() or proc.stderr.strip()


def check_2_serve(binary: str, workdir: str) -> tuple[str, str, OpencodeServer | None]:
    """2. serve slusa samo 127.0.0.1 i trazi lozinku."""
    server = OpencodeServer(binary, workdir)
    try:
        server.start()
    except OpencodeNotHealthy as exc:
        return "FAIL", str(exc), None
    if not server.requires_auth():
        server.close()
        return "FAIL", "endpoint dostupan BEZ lozinke", None
    return "PASS", f"{server.url} (auth obavezan)", server


def _run_agent(server: OpencodeServer, workdir: str, message: str,
               model: str | None) -> tuple[int, str, str]:
    cmd = [
        server.binary,
        "run",
        "--attach", server.url,
        "--password", server.password,
        "--agent", AGENT_ID,
        "--dir", workdir,
        "--format", "json",
    ]
    if model:
        cmd += ["--model", model]
    cmd.append(message)
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    return proc.returncode, proc.stdout, proc.stderr


def _looks_like_no_model(stderr: str) -> bool:
    lowered = stderr.lower()
    return any(hint in lowered for hint in NO_MODEL_HINTS)


def check_3_mcp_tool(server: OpencodeServer, workdir: str,
                     model: str | None) -> Result:
    """3. Agent pozove jedan MCP alat s laznim podacima."""
    if not model:
        return "SKIP", "model nije zadan (--model); bez kredencijala nema poziva"
    code, out, err = _run_agent(
        server, workdir,
        "Pozovi alat mujofix_get_system_info i ispisi polje marker.",
        model,
    )
    if code != 0:
        if _looks_like_no_model(err):
            return "SKIP", f"model nedostupan: {err.strip()[-200:]}"
        return "FAIL", f"agent run pao: {err.strip()[-300:]}"
    if SPIKE_MARKER in out:
        return "PASS", "agent vratio MCP marker iz laznih podataka"
    return "FAIL", "u izlazu nema ocekivanog MCP markera"


def check_4_shell_denied(server: OpencodeServer, workdir: str,
                         model: str | None) -> Result:
    """4. Pokušaj poziva shell-a mora biti odbijen."""
    if not model:
        return "SKIP", "model nije zadan (--model); zabrana nije dokaziva"
    code, out, err = _run_agent(
        server, workdir,
        "Pokreni shell komandu `whoami` i ispisi njen izlaz.",
        model,
    )
    combined = (out + err).lower()
    denied = any(
        word in combined
        for word in ("denied", "not allowed", "odbijen", "permission", "forbidden")
    )
    leaked_user = (
        code == 0 and not denied and len(out.strip()) > 0
        and "whoami" not in out.lower() and SPIKE_MARKER not in out
        and len(out.strip().splitlines()) <= 3
    )
    if denied:
        return "PASS", "poziv shell-a odbijen"
    if code != 0 and _looks_like_no_model(err):
        return "SKIP", f"model nedostupan: {err.strip()[-200:]}"
    if leaked_user:
        return "FAIL", f"shell IZLAZ procurio u odgovor: {out.strip()[:200]}"
    return "FAIL", f"neodluceno (code={code}): {(out + err).strip()[-300:]}"


def check_5_offline() -> Result:
    """5. Bez interneta/modela: offline fallback i dalje objasnjava nalaz."""
    text = offline_explain(
        {
            "title": "spike nalaz",
            "severity": "LOW",
            "evidence": "spike-fixture",
        }
    )
    if text and "OFFLINE" in text and "spike nalaz" in text:
        return "PASS", "offline fallback radi bez mreze i modela"
    return "FAIL", "offline fallback vratio prazno/neupotrebljivo"


def main() -> int:
    parser = argparse.ArgumentParser(description="MujoFix Faza 0 SPIKE")
    parser.add_argument("--model", default=os.environ.get("MUJOFIX_SPIKE_MODEL"),
                        help="npr. opencode-zen/gpt-5-nano (inace SKIP za 3/4)")
    parser.add_argument("--binary", default=None)
    args = parser.parse_args()

    if args.binary:
        os.environ["MUJOFIX_OPENCODE_BIN"] = args.binary

    print("MujoFix Faza 0 SPIKE (netestirano na Win10/11 dok se ne pokrene u VM-u)")
    status_1, binary, msg_1 = check_1_binary()
    print(f"CHECK 1 bundlovani binary bez Node-a: {status_1}: {msg_1}")
    if status_1 == "FAIL":
        return 1

    failed = False
    with tempfile.TemporaryDirectory(prefix="mujofix-spike-") as tmp:
        mcp_cmd = [sys.executable, os.path.abspath("mujofix/ai/mujofix_mcp.py")]
        write_config(tmp, mcp_cmd)
        status_2, msg_2, server = check_2_serve(binary, tmp)
        print(f"CHECK 2 serve 127.0.0.1 + lozinka: {status_2}: {msg_2}")
        if server is None:
            return 1
        try:
            for num, (status, msg) in (
                (3, check_3_mcp_tool(server, tmp, args.model)),
                (4, check_4_shell_denied(server, tmp, args.model)),
            ):
                print(f"CHECK {num} {'mcp alat' if num == 3 else 'shell zabrana'}: "
                      f"{status}: {msg}")
                failed |= status == "FAIL"
        finally:
            server.close()
        status_5, msg_5 = check_5_offline()
        print(f"CHECK 5 offline fallback: {status_5}: {msg_5}")
        failed |= status_5 == "FAIL"
    print("SPIKE GOTOV: " + ("IMA FAILOVA" if failed else "nema failova"))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

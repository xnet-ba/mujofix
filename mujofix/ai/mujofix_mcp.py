"""MujoFix MCP server (stdio, samo stdlib).

Izlozeni alati (nijedan ne mijenja sistem, samo citaju/vroliraju):
- get_findings, get_evidence, get_system_info, get_action_catalog (read-only)
- propose_plan (validira plan prema schemi + allowlisti; odbija sve izvan kataloga)

Podaci: --findings <json> s pravim izlazom scannera (Faza 4); bez argumenta
postoje od Faze 0 (spike); serviraju SAMO stvarne podatke. Transport: JSON-RPC 2.0, poruka po liniji.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

# MCP se pokrece i kao skripta po putanji (`python mujofix/ai/mujofix_mcp.py`),
# pa korijen repoa mora biti na sys.path da `import mujofix...` radi (i18n).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", ".."))

SERVER_NAME = "mujofix"
SERVER_VERSION = "0.0.1"
MAX_PLAN_STEPS = 20

# Faza 0 allowlista: samo 3 akcije iz specifikacije.
ACTION_ALLOWLIST = frozenset(
    {"disable_startup_item", "clean_temp", "restart_service"}
)

# Traga koji se nikad ne smiju pojaviti kao meta plana (tvrda zastita).
# Crna lista za AI predloge: substring provjera (namjerno "fail closed").
# NAMJERNO bez "c:\\windows" (preširoko — blokiralo bi i C:\Windows\Temp i WU
# cache, koji su legitimni ciljevi). Ne dira izvrsni sloj: executor vrti samo
# akcije iz kataloga nad nalazima koje je korisnik odabrao.
PROTECTED_HINTS = (
    "system32",
    "winsxs",
    "bitlocker",
    "program files",
    "\\documents",
    "\\pictures",
    "\\desktop",
    "\\downloads",
    "\\boot\\bcd",
    "defender",
)


def _is_protected(target: str) -> bool:
    lowered = (target or "").lower()
    return any(hint in lowered for hint in PROTECTED_HINTS)


def _target_problem(target: str) -> str:
    """Zasto meta nije upotrebljiva ("" = u redu). Mehanička provjera.

    Ne sudi o semantici akcije (to rade precondition akcije), ali odbija ocito
    smece: vise linija (injekcija), predugacko, bez ijednog slova (npr. "0") i
    tekst koji nije putanja/kljuc/ime.
    """
    if any(ch in target for ch in "\r\n\t"):
        return "sadrzi kontrolne znakove"
    if len(target) > 260:
        return "duze od 260 znakova"
    if not any(ch.isalpha() for ch in target):
        return "nema ni jedno slovo"
    return ""


def validate_plan(plan: object, lang: str = "bs") -> tuple[bool, str]:
    """Cista funkcija: (prihvacen, razlog). Nema nuspojava.

    `lang` odredjuje jezik razloga (korisnik ga vidi u logu kad AI plan padne);
    MCP alat ga zove bez jezika (model-facing tekst ostaje kanonski).
    """
    from mujofix.i18n.strings import tr

    def t(key: str, **fmt: object) -> str:
        return tr(key, lang, **fmt)

    if not isinstance(plan, dict):
        return False, t("vp_not_object")
    steps = plan.get("steps")
    if not isinstance(steps, list) or not steps:
        return False, t("vp_no_steps")
    if len(steps) > MAX_PLAN_STEPS:
        return False, t("vp_too_many", n=len(steps), max=MAX_PLAN_STEPS)
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            return False, t("vp_step_not_object", i=index)
        action = step.get("action")
        if not action or action not in ACTION_ALLOWLIST:
            return False, t("vp_unknown_action", i=index, a=action,
                            allowed=", ".join(sorted(ACTION_ALLOWLIST)))
        target = str(step.get("target", ""))
        if not target.strip():
            return False, t("vp_no_target", i=index)
        problem = _target_problem(target)
        if problem:
            return False, t("vp_bad_target", i=index, why=problem)
        if _is_protected(target):
            return False, t("vp_protected", i=index, p=target)
    return True, t("vp_ok", n=len(steps))


# Canary koji koristi scripts/phase0_spike.py: dokazuje da se sumnjiv tekst
# vrati modelu samo kao citirani podatak, nikad kao instrukcija. Nije podatak
# koji server izmislja (server vise ne servira nikakve lazne vrijednosti).
SPIKE_MARKER = "MUJOFIX-SPIKE-OK"

STORE: dict = {"findings": [], "system_info": None}


def load_findings_file(path: str) -> None:
    """Ucitaj pravi izlaz scannera: {"findings": [...], "system_info": {...}}."""
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or "findings" not in data:
        raise ValueError("findings fajl mora imati kljuc 'findings'")
    findings = data["findings"]
    if not isinstance(findings, list):
        raise ValueError("'findings' mora biti lista")
    if any(not isinstance(item, dict) for item in findings):
        raise ValueError("svaki nalaz mora biti objekat")
    STORE["findings"] = findings
    STORE["system_info"] = data.get("system_info")


NO_DATA_NOTE = (
    "No findings snapshot is loaded in this MCP process. In the live app the "
    "findings for this request are delivered as DATA in the user message; use "
    "them. Do not guess or invent anything, and do not report this tool's "
    "emptiness as 'no findings found'."
)


def _call_tool(name: str, args: dict) -> dict:
    if name == "get_findings":
        if not STORE["findings"]:
            return {"findings": [], "note": NO_DATA_NOTE}
        return {"findings": STORE["findings"]}
    if name == "get_evidence":
        wanted = args.get("finding_id")
        for finding in STORE["findings"]:
            if finding.get("id") == wanted:
                return {"finding_id": wanted,
                        "evidence": finding.get("evidence", {})}
        if STORE["findings"]:
            return {"finding_id": wanted, "evidence": {},
                    "error": "nepoznat finding_id"}
        return {"finding_id": wanted, "evidence": {}, "note": NO_DATA_NOTE}
    if name == "get_system_info":
        if STORE["system_info"] is not None:
            return STORE["system_info"]
        return {"system_info": None, "note": NO_DATA_NOTE}
    if name == "get_action_catalog":
        return {"actions": sorted(ACTION_ALLOWLIST)}
    if name == "propose_plan":
        ok, reason = validate_plan(args.get("plan"))
        if ok:
            return {"ok": True, "reason": reason}
        raise ValueError(reason)
    raise ValueError(f"nepoznat alat '{name}' (dozvoljeno: 5 mujofix alata)")


def _tools_list() -> list[dict]:
    def tool(name: str, desc: str, schema: dict) -> dict:
        return {
            "name": name,
            "description": desc,
            "inputSchema": schema,
        }

    obj = {"type": "object", "properties": {}}
    plan_schema = {
        "type": "object",
        "properties": {"plan": {"type": "object"}},
        "required": ["plan"],
    }
    return [
        tool("get_findings", "Read-only: lista nalaza scannera.", obj),
        tool(
            "get_evidence",
            "Read-only: dokaz za jedan nalaz.",
            {
                "type": "object",
                "properties": {"finding_id": {"type": "string"}},
                "required": ["finding_id"],
            },
        ),
        tool("get_system_info", "Read-only: osnovni podaci o sistemu.", obj),
        tool(
            "get_action_catalog",
            "Read-only: allowlista akcija koje plan smije predloziti.",
            obj,
        ),
        tool("propose_plan", "Validira plan prema schemi + allowlisti.", plan_schema),
    ]


def _tool_result(payload: object, is_error: bool = False) -> dict:
    """MCP `tools/call` rezultat po specu (2024-11-05): `content[]` + `isError`.

    Ranije se vracao goli objekat (npr. `{"actions": [...]}`), sto klijent
    (opencode/model) ne prikaze kako treba — model je video prazan/„Unknown"
    odgovor. Dokazano uzivo na pravom Windowsu sa gemini-2.5-flash.
    """
    return {
        "content": [{"type": "text",
                     "text": json.dumps(payload, ensure_ascii=False)}],
        "isError": bool(is_error),
    }


def handle_message(msg: object) -> dict | None:
    """Obradi jednu JSON-RPC poruku; NIKAD ne baca (vrati odgovor ili None).

    Granica je vanjski proces (opencode/model), pa neispravna poruka ne smije
    srusiti server: validan JSON koji nije objekat (npr. `[1,2]`), `params` koji
    nije objekat, ili nepoznat metod vracaju JSON-RPC gresku.
    """
    if not isinstance(msg, dict):
        return _error_response(None, "poruka mora biti JSON objekat")
    method = str(msg.get("method", ""))
    msg_id = msg.get("id")
    try:
        if method == "initialize":
            return _ok_response(msg_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            })
        if method == "tools/list":
            return _ok_response(msg_id, {"tools": _tools_list()})
        if method == "tools/call":
            params = msg.get("params")
            if not isinstance(params, dict):
                return _error_response(msg_id, "params mora biti objekat")
            arguments = params.get("arguments")
            if arguments is not None and not isinstance(arguments, dict):
                return _error_response(msg_id, "arguments mora biti objekat")
            try:
                payload = _call_tool(str(params.get("name", "")),
                                     arguments or {})
            except Exception as exc:  # greska ALATA ide kao isError rezultat
                return _ok_response(msg_id,
                                    _tool_result({"error": str(exc)},
                                                 is_error=True))
            return _ok_response(msg_id, _tool_result(payload))
        if msg_id is not None:
            return _error_response(msg_id, f"nepodrzan method '{method}'")
        return None
    except Exception as exc:  # granica: nikad ne srusi server
        return _error_response(msg_id, str(exc))


def _ok_response(msg_id: object, result: object) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _error_response(msg_id: object, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id,
            "error": {"code": -32602, "message": message}}


def _write(response: dict) -> None:
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()


def serve() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = handle_message(msg)
        if response is not None:
            _write(response)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MujoFix MCP server")
    parser.add_argument("--findings", default=os.environ.get("MUJOFIX_FINDINGS"),
                        help="JSON s pravim izlazom scannera")
    parsed = parser.parse_args()
    if parsed.findings:
        load_findings_file(parsed.findings)
    serve()

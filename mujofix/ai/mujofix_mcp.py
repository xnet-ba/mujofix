"""Minimalni MujoFix MCP server (stdio, samo stdlib) za Fazu 0 SPIKE.

Izlozeni alati (nijedan ne mijenja sistem, samo citaju/vroliraju):
- get_findings, get_evidence, get_system_info, get_action_catalog (read-only)
- propose_plan (validira plan prema allowlisti; odbija sve izvan kataloga)

Transport: JSON-RPC 2.0, jedna poruka po liniji na stdin/stdout.
"""

from __future__ import annotations

import json
import platform
import sys

SERVER_NAME = "mujofix"
SERVER_VERSION = "0.0.1"
SPIKE_MARKER = "MUJOFIX-SPIKE-OK"

# Faza 0 allowlista: samo 3 akcije iz specifikacije.
ACTION_ALLOWLIST = frozenset(
    {"disable_startup_item", "clean_temp", "restart_service"}
)

# Traga koji se nikad ne smiju pojaviti kao meta plana (tvrda zastita).
PROTECTED_HINTS = (
    "system32",
    "winsxs",
    "c:\\windows",
    "/windows/system32",
    "bitlocker",
)


def _is_protected(target: str) -> bool:
    lowered = (target or "").lower()
    return any(hint in lowered for hint in PROTECTED_HINTS)


def validate_plan(plan: object) -> tuple[bool, str]:
    """Cista funkcija: (prihvacen, razlog). Nema nuspojava."""
    if not isinstance(plan, dict):
        return False, "plan mora biti JSON objekat"
    steps = plan.get("steps")
    if not isinstance(steps, list) or not steps:
        return False, "plan mora imati nepraznu listu 'steps'"
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            return False, f"korak {index} nije objekat"
        action = step.get("action")
        if action not in ACTION_ALLOWLIST:
            return False, (
                f"korak {index}: akcija '{action}' nije u katalogu "
                f"{sorted(ACTION_ALLOWLIST)}"
            )
        target = str(step.get("target", ""))
        if not target:
            return False, f"korak {index}: nedostaje 'target'"
        if _is_protected(target):
            return False, f"korak {index}: zasticena zona '{target}'"
    return True, f"prihvaceno {len(steps)} koraka"


def _spike_system_info() -> dict:
    return {
        "spike": True,
        "marker": SPIKE_MARKER,
        "os": platform.system(),
        "note": "lazni podaci za Fazu 0 (stvarni scanneri dolaze u Fazi 1)",
    }


def _call_tool(name: str, args: dict) -> dict:
    if name == "get_findings":
        return {"findings": []}
    if name == "get_evidence":
        return {
            "finding_id": args.get("finding_id"),
            "evidence": "spike-fixture: nema stvarnih dokaza u Fazi 0",
        }
    if name == "get_system_info":
        return _spike_system_info()
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


def _respond(msg_id: object, result: object) -> None:
    sys.stdout.write(
        json.dumps({"jsonrpc": "2.0", "id": msg_id, "result": result}) + "\n"
    )
    sys.stdout.flush()


def _respond_error(msg_id: object, message: str) -> None:
    sys.stdout.write(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32602, "message": message},
            }
        )
        + "\n"
    )
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
        method = msg.get("method", "")
        msg_id = msg.get("id")
        try:
            if method == "initialize":
                _respond(
                    msg_id,
                    {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": SERVER_NAME,
                            "version": SERVER_VERSION,
                        },
                    },
                )
            elif method == "tools/list":
                _respond(msg_id, {"tools": _tools_list()})
            elif method == "tools/call":
                params = msg.get("params", {})
                _respond(
                    msg_id,
                    _call_tool(params.get("name", ""), params.get("arguments", {})),
                )
            elif msg_id is not None:
                _respond_error(msg_id, f"nepodrzan method '{method}'")
        except ValueError as exc:
            _respond_error(msg_id, str(exc))


if __name__ == "__main__":
    serve()

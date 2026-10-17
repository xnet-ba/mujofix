"""Mapiranje nalaza -> akcije kataloga (bez Qt-a, testabilno svuda).

Prazna lista = nalaz je samo preporuka (nema sigurne auto-popravke).
"""

from __future__ import annotations

from mujofix.actions.duplicates import QuarantineDuplicates
from mujofix.actions.env import FixTempVar, RemovePathEntry
from mujofix.actions.proxy import DisableProxy
from mujofix.actions.service import RestartService
from mujofix.actions.startup import DisableStartupItem
from mujofix.actions.temp import CleanTemp


def finding_to_actions(finding: dict) -> list:
    """Pretvori nalaz u akcije kataloga; prazno = samo preporuka."""
    fid = finding.get("id", "")
    evidence = finding.get("evidence", {})
    if fid == "disk-temp" and evidence.get("temp_dir"):
        return [CleanTemp(evidence["temp_dir"])]
    if fid == "disk-wu-cache" and evidence.get("path"):
        return [CleanTemp(evidence["path"])]
    if fid == "services-auto-stopped":
        return [RestartService(name) for name in evidence.get("sample", [])]
    if fid == "startup-count":
        actions = []
        for item in evidence.get("items", []):
            source = item.get("source", "")
            if "\\" in source and source[:4] in ("HKCU", "HKLM"):
                hive, path = source.split("\\", 1)
                actions.append(DisableStartupItem(hive, path, item["name"]))
        return actions
    if fid == "config-path-missing":
        return [RemovePathEntry(entry) for entry in evidence.get("entries", [])]
    if fid == "config-temp-var" and evidence.get("var"):
        return [FixTempVar(evidence["var"])]
    if fid == "network-proxy" and evidence.get("proxy", {}).get("registry"):
        return [DisableProxy()]
    if fid == "duplicates-found":
        groups = evidence.get("groups", [])
        if any(g.get("certain") and len(g.get("paths", [])) >= 2
               for g in groups):
            return [QuarantineDuplicates(groups)]
    return []

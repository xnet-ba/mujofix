"""Permisije scanner: iskljucen UAC, ranjive ACL dozvole, ne zasticeni share-ovi.

UAC OFF je CRITICAL nalaz (citamo, ne mijenjamo). icacls/net share se parsiraju
defanzivno: neprepoznat ispis = tihi skip te provjere, nikad laznih nalaza.
"""

from __future__ import annotations

import os
import re
import stat
import subprocess

from mujofix.core.models import Finding
from mujofix.platform import windows
from mujofix.scanners.base import ScanContext, Scanner, register

UAC_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
DEFAULT_SHARES = {"ADMIN$", "C$", "D$", "E$", "IPC$", "print$"}


def _uac_enabled() -> bool | None:
    try:
        values = windows.read_reg_values("HKLM", UAC_KEY)
    except windows.NotSupported:
        return None
    raw = values.get("EnableLUA")
    return None if raw is None else raw.strip() != "0"


def _icacls_writable_by(path: str, identities=("Everyone", "Users")) -> list[str]:
    """Vrati identitete s (W) pravom; prazno = cisto ili neparsirano (skip)."""
    try:
        proc = subprocess.run(["icacls", path], capture_output=True,
                              text=True, timeout=30)
    except OSError:
        return []
    if proc.returncode != 0:
        return []
    hits = []
    for line in proc.stdout.splitlines():
        for identity in identities:
            if identity in line and re.search(r":.*\(.*W.*\)", line):
                hits.append(identity)
    return sorted(set(hits))


def _net_shares() -> list[dict]:
    try:
        proc = subprocess.run(["net", "share"], capture_output=True,
                              text=True, timeout=30)
    except OSError:
        return []
    if proc.returncode != 0:
        return []
    shares, current = [], {}
    for line in proc.stdout.splitlines():
        name, _, rest = line.partition(" ")
        name = name.strip()
        if name and not name.startswith("-") and name != "Share name":
            if current.get("name"):
                shares.append(current)
            current = {"name": name, "resource": rest.strip()}
        elif "Path" in line or "Remark" in line:
            current["resource"] = line.split(None, 1)[-1].strip()
    if current.get("name"):
        shares.append(current)
    return [s for s in shares if s.get("name") not in DEFAULT_SHARES]


def _posix_world_writable(path: str) -> bool:
    try:
        return bool(os.stat(path).st_mode & stat.S_IWOTH)
    except OSError:
        return False


@register
class PermissionsScanner(Scanner):
    name = "permissions"

    def _scan(self, ctx: ScanContext) -> list[Finding]:
        findings: list[Finding] = []
        if windows.is_windows():
            uac = _uac_enabled()
            if uac is False:
                findings.append(Finding(
                    id="permissions-uac-off", scanner=self.name,
                    title="UAC (kontrola korisničkih naloga) je isključen",
                    why="Bez UAC-a svaki program tiho dobija admin prava — "
                        "najjaci sigurnosni mehanizam Windowsa ne radi.",
                    severity="CRITICAL",
                    impact="bilo koji program moze mijenjati sistem",
                    risk="nizak: ukljucivanje je reverzibilno (uz UAC prompt)",
                    reversible=True,
                    evidence={"EnableLUA": "0"},
                    tech_details=f"HKLM\\{UAC_KEY}"))
            sensitive = [os.environ.get("SystemRoot", r"C:\Windows"),
                         os.environ.get("ProgramFiles", r"C:\Program Files")]
            weak = [(p, _icacls_writable_by(p)) for p in sensitive
                    if os.path.isdir(p)]
            weak = [(p, ids) for p, ids in weak if ids]
            if weak:
                findings.append(Finding(
                    id="permissions-acl", scanner=self.name,
                    title="Preširoke dozvole na sistemskim folderima",
                    why="Obicni korisnici (ili Everyone) mogu pisati po "
                        "sistemskim folderima — podmetanje malware-a.",
                    severity="CRITICAL",
                    impact="moguce trajno kompromitovanje sistema",
                    risk="srednji: zatezanje ACL-a trazi oprez",
                    reversible=True,
                    evidence={"folders": [{"path": p, "writers": ids}
                                          for p, ids in weak]},
                    tech_details="icacls (W) grantovi"))
            shares = _net_shares()
            if shares:
                findings.append(Finding(
                    id="permissions-shares", scanner=self.name,
                    title=f"{len(shares)} nedefaultnih dijeljenih foldera",
                    why="Svaki share je ulaz u racunar s mreze; provjeri da "
                        "li su namjerni i kome su dostupni.",
                    severity="LOW", impact="moguci ulaz s mreze",
                    risk="nizak: gasenje sharea je reverzibilno",
                    reversible=True,
                    evidence={"shares": shares[:20]},
                    tech_details="net share"))
        else:
            writable = [entry for entry in
                        os.environ.get("PATH", "").split(os.pathsep)
                        if entry and _posix_world_writable(entry)]
            if writable:
                findings.append(Finding(
                    id="permissions-path-writable", scanner=self.name,
                    title="Svijet-zapisivi folderi u PATH-u",
                    why="Isto kao Windows verzija: podmetanje programa.",
                    severity="MEDIUM", impact="rizik podmetanja programa",
                    risk="nizak: skidanje prava je reverzibilno",
                    reversible=True,
                    evidence={"entries": writable[:20]},
                    tech_details="stat S_IWOTH (POSIX fallback)"))
        return findings

"""Mreza scanner: DNS razrjesavanje, latencija (TCP handshake, ne ping),
hosts hijack, proxy stanje, citljivost Winsock kataloga."""

from __future__ import annotations

import os
import socket
import subprocess
import time

from mujofix.core.models import Finding
from mujofix.platform import windows
from mujofix.scanners.base import ScanContext, Scanner, register

DNS_TEST_HOST = "example.com"
PROBE_TARGETS = (("1.1.1.1", 53), ("8.8.8.8", 53))
SLOW_MS = 1000.0
INTERNET_SETTINGS = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"

# domeni cije preusmjeravanje smrdi na hijack (ako ne vode na localhost)
HIJACK_KEYWORDS = ("microsoft", "windowsupdate", "google", "facebook",
                    "apple", "github", "bank", "paypal")
LOCAL_IPS = {"127.0.0.1", "::1"}


def _hosts_path() -> str:
    if windows.is_windows():
        root = os.environ.get("SystemRoot", r"C:\Windows")
        return os.path.join(root, "System32", "drivers", "etc", "hosts")
    return "/etc/hosts"


def _resolve(host: str) -> tuple[list[str], float]:
    started = time.time()
    infos = socket.getaddrinfo(host, 80)
    ips = sorted({info[4][0] for info in infos})
    return ips, (time.time() - started) * 1000.0


def _tcp_latency_ms(ip: str, port: int, timeout_s: float = 5.0) -> float | None:
    started = time.time()
    try:
        with socket.create_connection((ip, port), timeout=timeout_s):
            pass
    except OSError:
        return None
    return (time.time() - started) * 1000.0


def _read_hosts() -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    try:
        with open(_hosts_path(), encoding="utf-8", errors="replace") as handle:
            for line in handle:
                line = line.split("#", 1)[0].strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    entries.append((parts[0], parts[1]))
    except OSError:
        pass
    return entries


@register
class NetworkScanner(Scanner):
    name = "network"

    def _scan(self, ctx: ScanContext) -> list[Finding]:
        findings: list[Finding] = []
        try:
            ips, dns_ms = _resolve(DNS_TEST_HOST)
        except OSError as exc:
            return [Finding(
                id="network-dns", scanner=self.name,
                title=self.t("sc_net_dns_title"),
                why=self.t("sc_net_dns_why"),
                severity="CRITICAL",
                impact=self.t("sc_net_dns_impact"),
                risk=self.t("sc_net_check_risk"),
                reversible=False,
                evidence={"host": DNS_TEST_HOST, "error": str(exc)},
                tech_details="socket.getaddrinfo",
            )]
        evidence_net: dict = {"dns_host": DNS_TEST_HOST, "dns_ips": ips,
                              "dns_ms": round(dns_ms, 1)}
        best: float | None = None
        for ip, port in PROBE_TARGETS:
            latency = _tcp_latency_ms(ip, port)
            if latency is not None and (best is None or latency < best):
                best = latency
            if ctx.cancelled:
                return findings
        evidence_net["tcp_ms"] = round(best, 1) if best is not None else None
        if best is None:
            findings.append(Finding(
                id="network-unreachable", scanner=self.name,
                title=self.t("sc_net_unreachable_title"),
                why=self.t("sc_net_unreachable_why"),
                severity="MEDIUM", impact=self.t("sc_net_unreachable_impact"),
                risk=self.t("sc_net_check_risk"), reversible=False,
                evidence=evidence_net, tech_details="TCP connect :53"))
        elif best >= SLOW_MS:
            findings.append(Finding(
                id="network-slow", scanner=self.name,
                title=self.t("sc_net_slow_title", ms=f"{best:.0f}"),
                why=self.t("sc_net_slow_why"),
                severity="MEDIUM", impact=self.t("sc_net_slow_impact"),
                risk=self.t("sc_net_check_risk"), reversible=False,
                evidence=evidence_net, tech_details="TCP connect :53"))

        suspicious = [(ip, host) for ip, host in _read_hosts()
                      if ip not in LOCAL_IPS and any(
                          key in host.lower() for key in HIJACK_KEYWORDS)]
        if suspicious:
            findings.append(Finding(
                id="network-hosts", scanner=self.name,
                title=self.t("sc_net_hosts_title", n=len(suspicious)),
                why=self.t("sc_net_hosts_why"),
                severity="MEDIUM", impact=self.t("sc_net_hosts_impact"),
                risk=self.t("sc_net_hosts_risk"),
                reversible=True,
                evidence={"path": _hosts_path(),
                          "entries": suspicious[:20]},
                tech_details=f"parse({_hosts_path()})"))

        proxy: dict = {}
        if windows.is_windows():
            try:
                settings = windows.read_reg_values("HKCU", INTERNET_SETTINGS)
                if settings.get("ProxyEnable") == "1":
                    proxy["registry"] = settings.get("ProxyServer", "?")
            except windows.NotSupported:
                pass
        for var in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
            if os.environ.get(var):
                proxy[var] = self.t("sc_net_proxy_set")
        if proxy:
            findings.append(Finding(
                id="network-proxy", scanner=self.name,
                title=self.t("sc_net_proxy_title"),
                why=self.t("sc_net_proxy_why"),
                severity="LOW", impact=self.t("sc_net_proxy_impact"),
                risk=self.t("sc_net_proxy_risk"), reversible=True,
                evidence={"proxy": proxy},
                tech_details="registry Internet Settings + env"))

        if windows.is_windows() and not ctx.cancelled:
            proc = subprocess.run(["netsh", "winsock", "show", "catalog"],
                                  capture_output=True, text=True, timeout=60)
            if proc.returncode != 0:
                findings.append(Finding(
                    id="network-winsock", scanner=self.name,
                    title=self.t("sc_net_winsock_title"),
                    why=self.t("sc_net_winsock_why"),
                    severity="MEDIUM", impact=self.t("sc_net_winsock_impact"),
                    risk=self.t("sc_net_winsock_risk"),
                    reversible=False,
                    evidence={"error": proc.stderr.strip()[-200:]},
                    tech_details="netsh winsock show catalog"))
        return findings

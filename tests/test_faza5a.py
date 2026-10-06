"""Testovi Faze 5a: mreza i konfiguracija (mock socketa/subprocesa/env)."""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mujofix.scanners.base import ScanContext
from mujofix.scanners.config import ConfigScanner
from mujofix.scanners.network import NetworkScanner


def _socket_ok(*, latency_s=0.01):
    resolution = [("AF_INET", None, None, None, ("93.184.216.34", 80))]
    conn = MagicMock()
    conn.__enter__ = MagicMock(return_value=None)
    conn.__exit__ = MagicMock(return_value=False)
    return (patch("socket.getaddrinfo", return_value=resolution),
            patch("socket.create_connection", return_value=conn))


class TestNetworkScanner(unittest.TestCase):
    def run_scan(self):
        return NetworkScanner().scan(ScanContext())

    def test_dns_failure_is_critical(self):
        with patch("socket.getaddrinfo", side_effect=OSError("no dns")), \
             patch("mujofix.platform.windows.is_windows", return_value=False):
            report = self.run_scan()
        self.assertEqual(report.findings[0].id, "network-dns")
        self.assertEqual(report.findings[0].severity, "CRITICAL")

    def test_healthy_net_no_connectivity_findings(self):
        patches = _socket_ok()
        with patches[0], patches[1], \
             patch("mujofix.platform.windows.is_windows", return_value=False), \
             patch("mujofix.scanners.network._read_hosts", return_value=[]):
            report = self.run_scan()
        ids = {f.id for f in report.findings}
        self.assertNotIn("network-unreachable", ids)
        self.assertNotIn("network-slow", ids)

    def test_unreachable_probe(self):
        res, _ = _socket_ok()
        with res, \
             patch("socket.create_connection", side_effect=OSError("down")), \
             patch("mujofix.platform.windows.is_windows", return_value=False), \
             patch("mujofix.scanners.network._read_hosts", return_value=[]):
            report = self.run_scan()
        self.assertEqual(report.findings[0].id, "network-unreachable")

    def test_hosts_hijack_flagged(self):
        patches = _socket_ok()
        hosts = [("127.0.0.1", "localhost"),
                 ("93.184.216.34", "windowsupdate.microsoft.com")]
        with patches[0], patches[1], \
             patch("mujofix.platform.windows.is_windows", return_value=False), \
             patch("mujofix.scanners.network._read_hosts", return_value=hosts):
            report = self.run_scan()
        by_id = {f.id: f for f in report.findings}
        self.assertEqual(by_id["network-hosts"].severity, "MEDIUM")
        self.assertTrue(by_id["network-hosts"].reversible)

    def test_proxy_env_flagged_low(self):
        patches = _socket_ok()
        with patches[0], patches[1], \
             patch("mujofix.platform.windows.is_windows", return_value=False), \
             patch("mujofix.scanners.network._read_hosts", return_value=[]), \
             patch.dict(os.environ, {"HTTP_PROXY": "http://proxy:8080"}):
            report = self.run_scan()
        self.assertEqual(report.findings[-1].id, "network-proxy")
        self.assertEqual(report.findings[-1].severity, "LOW")


class TestConfigScanner(unittest.TestCase):
    def test_missing_and_writable_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            wide = os.path.join(tmp, "wide")
            os.mkdir(wide)
            os.chmod(wide, 0o777)
            env_path = os.pathsep.join([wide, os.path.join(tmp, "nepostoji")])
            with patch.dict(os.environ, {"PATH": env_path,
                                          "TEMP": tmp, "TMP": tmp}), \
                 patch("mujofix.platform.windows.is_windows", return_value=False):
                report = ConfigScanner().scan(ScanContext())
        by_id = {f.id: f for f in report.findings}
        self.assertIn(wide, by_id["config-path-writable"].evidence["entries"])
        self.assertEqual(by_id["config-path-missing"].severity, "LOW")

    def test_bad_temp_var(self):
        with patch.dict(os.environ, {"PATH": "", "TEMP": "/ne/postoji",
                                      "TMP": "/ne/postoji"}), \
             patch("mujofix.platform.windows.is_windows", return_value=False):
            report = ConfigScanner().scan(ScanContext())
        ids = {f.id for f in report.findings}
        self.assertIn("config-temp-var", ids)

    def test_windows_skips_stat_writable_check(self):
        # Regresija s pravog Win runnera: stat bitovi tamo varaju (Temp je
        # uredno per-user, a S_IWOTH je postavljen) — to pokriva icacls provjera.
        with tempfile.TemporaryDirectory() as tmp:
            wide = os.path.join(tmp, "wide")
            os.mkdir(wide)
            os.chmod(wide, 0o777)
            env_path = os.pathsep.join([wide, os.path.join(tmp, "nepostoji")])
            with patch.dict(os.environ, {"PATH": env_path,
                                          "TEMP": tmp, "TMP": tmp}), \
                 patch("mujofix.platform.windows.is_windows", return_value=True):
                report = ConfigScanner().scan(ScanContext())
        ids = {f.id for f in report.findings}
        self.assertNotIn("config-path-writable", ids)
        self.assertIn("config-path-missing", ids)

    def test_clean_env_no_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"PATH": tmp, "TEMP": tmp,
                                          "TMP": tmp}), \
                 patch("mujofix.platform.windows.is_windows", return_value=False):
                report = ConfigScanner().scan(ScanContext())
        self.assertEqual(report.findings, [])


if __name__ == "__main__":
    unittest.main()

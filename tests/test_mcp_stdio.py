import json
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mujofix.ai.agent_config import mcp_command


class TestMcpCommand(unittest.TestCase):
    def test_dev_form_uses_cli_mcp_subcommand(self):
        cmd = mcp_command()
        self.assertEqual(cmd[1:], ["-m", "mujofix.cli", "mcp"])

    def test_frozen_form_uses_console_cli_exe(self):
        import mujofix.ai.agent_config as mod
        had_frozen = hasattr(sys, "frozen")
        old_exe = sys.executable
        sys.frozen = True
        sys.executable = "/App/MujoFix.exe"
        try:
            cmd = mod.mcp_command()
        finally:
            if not had_frozen:
                del sys.frozen
            sys.executable = old_exe
        exe = "MujoFixCLI.exe" if os.name == "nt" else "MujoFixCLI"
        self.assertEqual(cmd, [os.path.join("/App", exe), "mcp"])


class TestMcpStdioSurface(unittest.TestCase):
    """Stvarni MCP handshake protiv `mujofix.cli mcp` (bez modela, bez mreze)."""

    @classmethod
    def setUpClass(cls):
        cls.proc = subprocess.Popen(
            [sys.executable, "-m", "mujofix.cli", "mcp"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            text=True, bufsize=1,
            cwd=os.path.join(os.path.dirname(__file__), ".."))

    @classmethod
    def tearDownClass(cls):
        cls.proc.stdin.close()
        cls.proc.wait(timeout=10)

    def _rpc(self, payload: dict) -> dict:
        self.proc.stdin.write(json.dumps(payload) + "\n")
        self.proc.stdin.flush()
        for _ in range(5):
            line = self.proc.stdout.readline()
            if not line:
                break
            try:
                got = json.loads(line)
            except json.JSONDecodeError:
                continue
            if got.get("id") == payload.get("id"):
                return got
        raise AssertionError("nema odgovora na JSON-RPC")

    def test_initialize_and_tools_list(self):
        init = self._rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                          "params": {"protocolVersion": "2024-11-05"}})
        self.assertEqual(init["result"]["protocolVersion"], "2024-11-05")
        tools = self._rpc({"jsonrpc": "2.0", "id": 2,
                           "method": "tools/list"})["result"]["tools"]
        names = sorted(t["name"] for t in tools)
        self.assertEqual(names, ["get_action_catalog", "get_evidence",
                                 "get_findings", "get_system_info",
                                 "propose_plan"])

    def test_catalog_is_read_only_sorted(self):
        got = self._rpc({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                         "params": {"name": "get_action_catalog",
                                    "arguments": {}}})
        actions = got["result"]["actions"]
        self.assertEqual(actions, sorted(actions))
        self.assertTrue(actions)

    def test_unknown_tool_is_an_error(self):
        got = self._rpc({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                         "params": {"name": "bash", "arguments": {}}})
        self.assertIn("error", got)
        self.assertNotIn("result", got)


if __name__ == "__main__":
    unittest.main()

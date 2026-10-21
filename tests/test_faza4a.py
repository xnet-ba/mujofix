"""Testovi Faze 4a: lanac, retry/backoff, offline, anonimizacija, plan-parse."""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mujofix.ai.provider import (
    AIRequest,
    FallbackChain,
    OfflineProvider,
    OpenCodeProvider,
    Provider,
    ProviderError,
    build_chain,
    build_prompt,
    compact_findings,
    extract_plan,
    free_zen_models,
    plan_lines,
)
from mujofix.ai.sanitize import DROP_KEYS, sanitize


class FailProvider(Provider):
    name = "fail"

    def __init__(self, times: int):
        self.times = times
        self.calls = 0

    def explain(self, request):
        self.calls += 1
        if self.calls <= self.times:
            raise ProviderError("rate limit")
        from mujofix.ai.provider import AIResponse
        return AIResponse(text="ok", model="fail", plan=None)


class TestFallbackChain(unittest.TestCase):
    def req(self):
        return AIRequest(findings=[{"id": "a", "title": "t", "why": "w",
                                    "severity": "LOW", "impact": "i",
                                    "evidence": {"n": 1}}])

    def test_first_working_wins(self):
        chain = FallbackChain([FailProvider(0), OfflineProvider()],
                              sleep_fn=lambda s: None)
        resp = chain.explain(self.req())
        self.assertEqual(resp.text, "ok")
        self.assertFalse(resp.offline)

    def test_retry_then_next(self):
        flaky = FailProvider(1)
        sleeps: list[float] = []
        chain = FallbackChain([flaky, OfflineProvider()], retries=2,
                              sleep_fn=sleeps.append)
        resp = chain.explain(self.req())
        self.assertEqual(resp.text, "ok")
        self.assertEqual(flaky.calls, 2)
        self.assertEqual(sleeps, [1])  # jedan fail -> sleep(2**0), pa uspjeh

    def test_all_fail_goes_offline(self):
        chain = FallbackChain([FailProvider(99), OfflineProvider()], retries=0,
                              sleep_fn=lambda s: None)
        resp = chain.explain(self.req())
        self.assertTrue(resp.offline and resp.model == "offline")
        # lanac BEZ offline providera: sufiks s razlogom, aplikacija radi dalje
        chain2 = FallbackChain([FailProvider(99)], retries=0,
                               sleep_fn=lambda s: None)
        resp2 = chain2.explain(self.req())
        self.assertTrue(resp2.offline)
        self.assertIn("AI nedostupan", resp2.text)

    def test_sent_log_is_sanitized(self):
        req = AIRequest(
            findings=[{"id": "a", "title": "greska na 192.168.1.5",
                       "why": "w", "severity": "LOW", "impact": "i",
                       "evidence": {"token": "tajna", "ip": "10.0.0.7"}}],
            username="admir", hostname="PC-ADMIR")
        chain = FallbackChain([OfflineProvider()], sleep_fn=lambda s: None)
        chain.explain(req)
        logged = str(chain.sent_log)
        self.assertNotIn("192.168.1.5", logged)
        self.assertNotIn("10.0.0.7", logged)
        self.assertNotIn("admir", logged.lower())
        self.assertNotIn("tajna", logged)


class TestFallbackChainSanitizesPayload(unittest.TestCase):
    """Poslano modelu MORA biti anonimizirano — i isto kao na ekranu log-a."""

    class CapturingProvider(Provider):
        name = "capture"

        def __init__(self):
            self.seen = None

        def explain(self, request):
            self.seen = request
            return AIResponse(text="ok", model=self.name)

    def _finding(self):
        return {"id": "f1", "title": "Temp", "severity": "LOW",
                "evidence": {"path": r"C:\Users\marko\AppData\Local\Temp\x.tmp",
                             "ip": "192.168.1.50",
                             "mac": "AA:BB:CC:DD:EE:FF",
                             "password": "tajna"}}

    def test_model_gets_redacted_findings_not_raw(self):
        provider = self.CapturingProvider()
        chain = FallbackChain([provider])
        chain.explain(AIRequest([self._finding()], "marko", "PC-MARKO"))
        blob = json.dumps(provider.seen.findings, ensure_ascii=False)
        self.assertNotIn("marko", blob)
        self.assertNotIn("192.168.1.50", blob)
        self.assertNotIn("AA:BB:CC:DD:EE:FF", blob)
        self.assertNotIn("tajna", blob)
        self.assertIn("<korisnik>", blob)
        self.assertIn("<ip>", blob)

    def test_log_equals_what_provider_received(self):
        provider = self.CapturingProvider()
        chain = FallbackChain([provider])
        chain.explain(AIRequest([self._finding()], "marko", "PC-MARKO"))
        self.assertEqual(chain.sent_log[0]["findings"],
                         provider.seen.findings)

    def test_consent_example_is_exactly_the_sent_prompt(self):
        """Ekran pristanka mora prikazati isti tekst koji odlazi modelu."""
        raw = [self._finding()]
        example = build_prompt(sanitize(compact_findings(raw), "marko", "PC-MARKO"))
        provider = self.CapturingProvider()
        FallbackChain([provider]).explain(AIRequest(raw, "marko", "PC-MARKO"))
        self.assertEqual(example, provider.seen and
                         build_prompt(provider.seen.findings))



class TestPlanLines(unittest.TestCase):
    def test_renders_known_actions_with_labels_and_targets(self):
        lines = plan_lines({"steps": [
            {"action": "clean_temp", "target": r"C:\Users\x\Temp"},
            {"action": "restart_service", "target": "Spooler"},
        ]})
        self.assertEqual(len(lines), 2)
        self.assertIn("Ocisti privremene fajlove", lines[0])
        self.assertIn(r"C:\Users\x\Temp", lines[0])
        self.assertIn("Restartuj servis", lines[1])

    def test_unknown_action_shows_raw_name_never_hides_it(self):
        lines = plan_lines({"steps": [{"action": "rm_rf"}]})
        self.assertEqual(lines, ["1. rm_rf"])

    def test_empty_and_malformed_plans_are_safe(self):
        self.assertEqual(plan_lines(None), [])
        self.assertEqual(plan_lines({}), [])
        self.assertEqual(plan_lines({"steps": ["nope", {"action": "clean_temp"}]}),
                         ["1. Ocisti privremene fajlove"])

class TestBackoffValues(unittest.TestCase):
    def test_backoff_sequence(self):
        # retries=2, fail 3x pa offline: sleep 1, 2 (2**0, 2**1)
        sleeps: list[float] = []
        chain = FallbackChain([FailProvider(99)], retries=2,
                              sleep_fn=sleeps.append)
        chain.explain(AIRequest(findings=[]))
        self.assertEqual(sleeps, [1, 2])


class TestSanitize(unittest.TestCase):
    def test_user_host_ip_mac_dropped(self):
        obj = {"title": "C:\\Users\\Admir\\x na PC-ADMIR 192.168.1.5 "
                        "AA:BB:CC:DD:EE:FF",
               "password": "hunter2", "other": "ok"}
        out = sanitize(obj, username="Admir", hostname="PC-ADMIR")
        text = str(out)
        self.assertNotIn("Admir", text)
        self.assertNotIn("192.168.1.5", text)
        self.assertNotIn("AA:BB:CC:DD:EE:FF", text)
        self.assertNotIn("hunter2", text)
        self.assertIn("<korisnik>", text)

    def test_drop_keys_case_insensitive(self):
        for key in DROP_KEYS:
            out = sanitize({key.upper(): "v"})
            self.assertEqual(out[key.upper()], "<uklonjeno>")


class TestPlanParse(unittest.TestCase):
    def test_extracts_last_json_block(self):
        text = ('bla ```json {"a": 1} ``` jos ```json '
                '{"steps": [{"action": "clean_temp", "target": "T"}]} ```')
        plan = extract_plan(text)
        self.assertEqual(plan["steps"][0]["action"], "clean_temp")

    def test_none_without_block(self):
        self.assertIsNone(extract_plan("nema bloka"))

    def test_none_on_bad_json(self):
        self.assertIsNone(extract_plan("```json {ne valja} ```"))

    def test_compact_limits_and_fields(self):
        findings = [{"id": str(i), "title": "t", "why": "w",
                     "severity": "LOW", "impact": "i",
                     "password": "x", "evidence": {}} for i in range(30)]
        compact = compact_findings(findings)
        self.assertEqual(len(compact), 10)
        self.assertNotIn("password", compact[0])

    def test_free_zen_filter(self):
        models = ["opencode/big-pickle", "opencode/deepseek-v4.1-flash-free",
                  "opencode/orion-pro", "anthropic/claude", "openai/gpt-5",
                  "openrouter/google/gemma-4-31b-it:free", "opencode/beam-free"]
        self.assertEqual(free_zen_models(models),
                         ["opencode/big-pickle",
                          "opencode/deepseek-v4.1-flash-free",
                          "opencode/beam-free"])


def boom(*_a, **_k):
    raise AssertionError("ovo se ne smije pozvati bez pristanka/na putu")


class TestBuildChain(unittest.TestCase):
    """build_chain: offline default, ziv Zen samo uz pristanak, nikad ne baca.

    MujoFix ne dizemo server — lanac se gradi, a `opencode run` se pokrece tek
    pri objasnjenju (kao child proces).
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.wd = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def test_writes_agent_config_for_run(self):
        """Bez opencode.json `run --agent mujofix` ne bi nasao agenta ni MCP."""
        build_chain(True, self.wd, binary="/x/opencode",
                    model_lister=lambda _b: ["opencode/beam-free"])
        with open(os.path.join(self.wd, "opencode.json"), encoding="utf-8") as fh:
            cfg = json.load(fh)
        self.assertIn("mujofix", cfg["agent"])
        self.assertIn("mujofix", cfg["mcp"])

    def test_consent_off_is_offline_and_no_spawn(self):
        session = build_chain(False, self.wd, binary="/x/opencode",
                              model_lister=boom)
        self.assertFalse(session.live)
        self.assertIn("pristanak", session.note)
        self.assertEqual(len(session.chain.providers), 1)
        self.assertIsInstance(session.chain.providers[0], OfflineProvider)

    def test_missing_binary_is_offline(self):
        from mujofix.ai import opencode_runtime
        with patch.object(opencode_runtime, "bundled_binary",
                          side_effect=opencode_runtime.OpencodeNotFound("nema")):
            session = build_chain(True, self.wd)
        self.assertFalse(session.live)
        self.assertIn("OpenCode", session.note)

    def test_model_lister_failure_is_offline(self):
        session = build_chain(True, self.wd, binary="/x/opencode",
                              model_lister=boom)
        self.assertFalse(session.live)
        self.assertIn("zivi model nedostupan", session.note)

    def test_no_free_model_is_offline(self):
        session = build_chain(True, self.wd, binary="/x/opencode",
                              model_lister=lambda _b: ["anthropic/claude"])
        self.assertFalse(session.live)
        self.assertIn("nema besplatnog Zen modela", session.note)

    def test_live_chain_prefers_free_marker_over_stealth(self):
        session = build_chain(True, self.wd, binary="/x/opencode",
                              model_lister=lambda _b: ["opencode/big-pickle",
                                                       "opencode/beam-free"])
        self.assertTrue(session.live)
        self.assertIn("opencode/beam-free", session.note)
        first, last = session.chain.providers[0], session.chain.providers[-1]
        self.assertIsInstance(first, OpenCodeProvider)
        self.assertEqual(first.model, "opencode/beam-free")
        self.assertIsInstance(last, OfflineProvider)

    def test_live_provider_env_isolates_config_home(self):
        """Bez XDG_CONFIG_HOME nas config se stapa sa korisnickim globalnim."""
        session = build_chain(True, self.wd, binary="/x/opencode",
                              model_lister=lambda _b: ["opencode/a-free"])
        provider = session.chain.providers[0]
        xdg = (provider.env or {}).get("XDG_CONFIG_HOME")
        self.assertTrue(xdg)
        self.assertTrue(xdg.startswith(self.wd))


class TestIsolatedConfigHome(unittest.TestCase):
    def test_config_home_is_inside_workdir_and_created(self):
        from mujofix.ai.agent_config import config_home
        with tempfile.TemporaryDirectory() as wd:
            path = config_home(wd)
            self.assertTrue(path.startswith(wd))
            self.assertTrue(os.path.isdir(path))

    def test_build_chain_isolates_global_config(self):
        """Bez XDG_CONFIG_HOME nas agent naslijedi globalne MCP/pluginove."""
        with tempfile.TemporaryDirectory() as wd:
            session = build_chain(True, wd, binary="/bin/true",
                                  model_lister=lambda _b: ["opencode/a-free"])
            self.assertTrue(session.live)
            env = session.chain.providers[0].env or {}
        self.assertTrue((env.get("XDG_CONFIG_HOME") or "").startswith(wd))


class TestOpenCodeProviderCmd(unittest.TestCase):
    def _provider(self):
        return OpenCodeProvider("/x/opencode", "/tmp", "opencode/beam-free")

    def test_cmd_has_no_forbidden_flag_and_uses_text_output(self):
        from mujofix.ai.opencode_runtime import FORBIDDEN_FLAGS
        cmd = self._provider()._cmd("ping")
        for flag in FORBIDDEN_FLAGS:
            self.assertNotIn(flag, cmd)
        # --format json = raw event stream; plan se cita iz teksta → ne smije.
        self.assertNotIn("--format", cmd)
        # Nema lokalnog backend-a: nista sto pokazuje na server.
        for flag in ("--attach", "--password", "--port", "--hostname"):
            self.assertNotIn(flag, cmd)
        self.assertEqual(cmd[cmd.index("--agent") + 1], "mujofix")
        self.assertEqual(cmd[cmd.index("--dir") + 1], "/tmp")
        self.assertEqual(cmd[cmd.index("--model") + 1], "opencode/beam-free")

    def test_forbidden_flag_would_raise(self):
        provider = self._provider()
        provider.workdir = "--auto"
        self.assertRaises(ProviderError, provider._cmd, "ping")


if __name__ == "__main__":
    unittest.main()

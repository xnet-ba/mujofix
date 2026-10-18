"""Testovi Faze 4a: lanac, retry/backoff, offline, anonimizacija, plan-parse."""

import os
import sys
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
    compact_findings,
    extract_plan,
    free_zen_models,
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


class FakeServer:
    def __init__(self, fail_start: bool = False):
        self.started = 0
        self.closed = 0
        self.fail_start = fail_start
        self.url = "http://127.0.0.1:9"
        self.password = "pw"

    def start(self):
        self.started += 1
        if self.fail_start:
            raise RuntimeError("port zauzet")
        return self

    def close(self):
        self.closed += 1


def boom(*_a, **_k):
    raise AssertionError("server se ne smije dizati bez pristanka")


class TestBuildChain(unittest.TestCase):
    """build_chain: offline default, ziv Zen samo uz pristanak, nikad ne baca."""

    def test_consent_off_is_offline_and_no_spawn(self):
        session = build_chain(False, "/tmp", binary="/x/opencode",
                              server_factory=boom, model_lister=boom)
        self.assertFalse(session.live)
        self.assertIn("pristanak", session.note)
        self.assertEqual(len(session.chain.providers), 1)
        self.assertIsInstance(session.chain.providers[0], OfflineProvider)

    def test_missing_binary_is_offline(self):
        from mujofix.ai import opencode_runtime
        with patch.object(opencode_runtime, "bundled_binary",
                          side_effect=opencode_runtime.OpencodeNotFound("nema")):
            session = build_chain(True, "/tmp", server_factory=boom)
        self.assertFalse(session.live)
        self.assertIn("OpenCode", session.note)

    def test_server_failure_closes_process_and_falls_back(self):
        server = FakeServer(fail_start=True)

        def factory(_bin, _dir):
            return server

        session = build_chain(True, "/tmp", binary="/x/opencode",
                              server_factory=factory,
                              model_lister=lambda _b: ["opencode/beam-free"])
        self.assertFalse(session.live)
        self.assertEqual(server.started, 1)
        self.assertEqual(server.closed, 1)
        self.assertIn("zivi model nedostupan", session.note)

    def test_no_free_model_closes_server(self):
        server = FakeServer()
        session = build_chain(True, "/tmp", binary="/x/opencode",
                              server_factory=lambda _b, _d: server,
                              model_lister=lambda _b: ["anthropic/claude"])
        self.assertFalse(session.live)
        self.assertEqual(server.closed, 1)
        self.assertIn("nema besplatnog Zen modela", session.note)

    def test_live_chain_prefers_free_marker_over_stealth(self):
        server = FakeServer()
        session = build_chain(True, "/tmp", binary="/x/opencode",
                              server_factory=lambda _b, _d: server,
                              model_lister=lambda _b: ["opencode/big-pickle",
                                                       "opencode/beam-free"])
        self.assertTrue(session.live)
        self.assertIn("opencode/beam-free", session.note)
        first, last = session.chain.providers[0], session.chain.providers[-1]
        self.assertIsInstance(first, OpenCodeProvider)
        self.assertEqual(first.model, "opencode/beam-free")
        self.assertIsInstance(last, OfflineProvider)
        session.close()
        self.assertEqual(server.closed, 1)
        session.close()  # idempotentno: drugi close ne dira server ponovo
        self.assertEqual(server.closed, 1)


if __name__ == "__main__":
    unittest.main()

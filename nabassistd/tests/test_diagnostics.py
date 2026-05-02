import unittest

from nabassistd.config import AssistConfig, WakeWordConfig, WakeWordEngineName
from nabassistd.diagnostics import overall_ok, run_diagnostics


class FakeClient:
    def __init__(self, ping_ok=True):
        self.ping_ok = ping_ok
        self.disconnected = False

    async def ping(self, timeout=2.0):
        return self.ping_ok

    async def disconnect(self):
        self.disconnected = True


class TestAssistDiagnostics(unittest.IsolatedAsyncioTestCase):
    async def test_remote_wake_word_success(self):
        client = FakeClient(ping_ok=True)
        config = AssistConfig(
            enabled=True,
            wake_word=WakeWordConfig(engine=WakeWordEngineName.REMOTE),
        )

        results = await run_diagnostics(
            config, client_factory=lambda config: client
        )

        self.assertTrue(overall_ok(results))
        self.assertTrue(client.disconnected)

    async def test_reports_disabled_assist_and_ping_failure(self):
        client = FakeClient(ping_ok=False)
        config = AssistConfig(
            enabled=False,
            wake_word=WakeWordConfig(engine=WakeWordEngineName.REMOTE),
        )

        results = await run_diagnostics(
            config, client_factory=lambda config: client
        )

        self.assertFalse(overall_ok(results))
        self.assertEqual(results[0].name, "assist_enabled")
        self.assertFalse(results[0].ok)
        self.assertEqual(results[2].name, "wyoming_ping")
        self.assertFalse(results[2].ok)


if __name__ == "__main__":
    unittest.main()

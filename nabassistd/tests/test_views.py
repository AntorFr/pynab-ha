from unittest.mock import patch

from django.test import Client, TestCase

from nabassistd.config import WakeWordEngineName
from nabassistd.diagnostics import DiagnosticResult
from nabassistd.models import Config


class TestSettingsView(TestCase):
    def test_get_settings(self):
        client = Client()
        response = client.get("/nabassistd/settings")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.templates[0].name, "nabassistd/settings.html"
        )
        self.assertTrue("config" in response.context)
        config = Config.load()
        self.assertEqual(response.context["config"], config)
        self.assertFalse(config.enabled)
        self.assertEqual(config.wake_word_engine, "micro")
        self.assertEqual(config.wake_word_model, "okay_nabu")
        self.assertContains(
            response,
            'name="wake_word_sensitivity" type="number" min="0" max="1" step="0.05" class="form-control" value="0.5"',
        )
        self.assertContains(
            response,
            'name="pre_roll_seconds" type="number" min="0.1" max="5" step="0.1" class="form-control" value="1.0"',
        )

    def test_set_settings(self):
        client = Client()
        response = client.post(
            "/nabassistd/settings",
            {
                "enabled": "on",
                "satellite_name": "Lapin",
                "wyoming_host": "ha.local",
                "wyoming_port": "10300",
                "wake_word_engine": "openwakeword",
                "wake_word_model": "hey_jarvis",
                "wake_word_sensitivity": "0.7",
                "pre_roll_seconds": "1.5",
                "fallback_to_remote": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        config = Config.load()
        self.assertTrue(config.enabled)
        self.assertEqual(config.satellite_name, "Lapin")
        self.assertEqual(config.wyoming_host, "ha.local")
        self.assertEqual(config.wyoming_port, 10300)
        self.assertEqual(config.wake_word_engine, "openwakeword")
        self.assertEqual(config.wake_word_model, "hey_jarvis")
        self.assertEqual(config.wake_word_sensitivity, 0.7)
        self.assertEqual(config.pre_roll_seconds, 1.5)
        self.assertTrue(config.fallback_to_remote)

    def test_diagnostics_uses_posted_settings_without_saving(self):
        client = Client()

        async def fake_run_diagnostics(config):
            self.assertTrue(config.enabled)
            self.assertEqual(config.satellite_name, "Lapin")
            self.assertEqual(config.wyoming_host, "ha.local")
            self.assertEqual(config.wyoming_port, 10300)
            self.assertEqual(
                config.wake_word.engine, WakeWordEngineName.REMOTE
            )
            self.assertEqual(config.wake_word.model, "okay_nabu")
            self.assertEqual(config.wake_word.sensitivity, 0.8)
            self.assertEqual(config.wake_word.pre_roll_seconds, 2.0)
            self.assertTrue(config.wake_word.fallback_to_remote)
            return [
                DiagnosticResult("assist_enabled", True, "Assist is enabled"),
                DiagnosticResult("wyoming_ping", False, "No pong"),
            ]

        with patch(
            "nabassistd.views.run_diagnostics",
            side_effect=fake_run_diagnostics,
        ):
            response = client.post(
                "/nabassistd/diagnostics",
                {
                    "enabled": "on",
                    "satellite_name": "Lapin",
                    "wyoming_host": "ha.local",
                    "wyoming_port": "10300",
                    "wake_word_engine": "remote",
                    "wake_word_model": "okay_nabu",
                    "wake_word_sensitivity": "0.8",
                    "pre_roll_seconds": "2.0",
                    "fallback_to_remote": "on",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "results": [
                    {
                        "name": "assist_enabled",
                        "ok": True,
                        "message": "Assist is enabled",
                    },
                    {
                        "name": "wyoming_ping",
                        "ok": False,
                        "message": "No pong",
                    },
                ]
            },
        )
        self.assertEqual(Config.load().wyoming_host, "homeassistant.local")

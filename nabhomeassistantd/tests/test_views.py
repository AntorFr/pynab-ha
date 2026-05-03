from django.test import Client, TestCase

from nabhomeassistantd.models import Config


class TestSettingsView(TestCase):
    def test_get_settings(self):
        client = Client()
        response = client.get("/nabhomeassistantd/settings")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.templates[0].name, "nabhomeassistantd/settings.html"
        )
        self.assertFalse(response.context["config"].enabled)

    def test_set_settings(self):
        client = Client()
        response = client.post(
            "/nabhomeassistantd/settings",
            {
                "enabled": "on",
                "mqtt_host": "ha.local",
                "mqtt_port": "1884",
                "mqtt_username": "user",
                "mqtt_password": "secret",
                "device_name": "Lapin",
                "discovery_prefix": "homeassistant",
                "topic_prefix": "pynab_lapin",
            },
        )

        self.assertEqual(response.status_code, 200)
        config = Config.load()
        self.assertTrue(config.enabled)
        self.assertEqual(config.mqtt_host, "ha.local")
        self.assertEqual(config.mqtt_port, 1884)
        self.assertEqual(config.mqtt_username, "user")
        self.assertEqual(config.mqtt_password, "secret")
        self.assertEqual(config.device_name, "Lapin")
        self.assertEqual(config.discovery_prefix, "homeassistant")
        self.assertEqual(config.topic_prefix, "pynab_lapin")

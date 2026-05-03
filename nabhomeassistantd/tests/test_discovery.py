import json
import unittest

from nabhomeassistantd.config import HomeAssistantConfig
from nabhomeassistantd.discovery import HomeAssistantDiscovery


class TestHomeAssistantDiscovery(unittest.TestCase):
    def test_builds_state_and_button_discovery_messages(self):
        discovery = HomeAssistantDiscovery(
            HomeAssistantConfig(
                device_name="Lapin",
                discovery_prefix="homeassistant",
                topic_prefix="pynab_lapin",
            )
        )

        messages = list(discovery.discovery_messages())

        self.assertEqual(
            [message.topic for message in messages],
            [
                "homeassistant/sensor/pynab_lapin/state/config",
                "homeassistant/button/pynab_lapin/sleep/config",
                "homeassistant/button/pynab_lapin/wakeup/config",
                "homeassistant/number/pynab_lapin/volume/config",
                "homeassistant/switch/pynab_lapin/mute/config",
            ],
        )
        state_payload = json.loads(messages[0].payload)
        self.assertEqual(state_payload["name"], "State")
        self.assertEqual(state_payload["state_topic"], "pynab_lapin/state")
        self.assertEqual(state_payload["device"]["name"], "Lapin")

    def test_command_topics(self):
        discovery = HomeAssistantDiscovery(HomeAssistantConfig())

        self.assertEqual(
            discovery.command_topics(),
            [
                "pynab/command/sleep",
                "pynab/command/wakeup",
                "pynab/command/volume",
                "pynab/command/mute",
            ],
        )

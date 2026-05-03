import unittest

from nabhomeassistantd.config import HomeAssistantConfig
from nabhomeassistantd.nabhomeassistantd import NabHomeAssistantd


class FakeMqttClient:
    def __init__(self):
        self.published = []
        self.subscribed = []
        self.connected = None
        self.loop_started = False
        self.loop_stopped = False
        self.disconnected = False
        self.on_message = None

    def will_set(self, topic, payload, retain=False):
        self.will = (topic, payload, retain)

    def username_pw_set(self, username, password):
        self.credentials = (username, password)

    def connect(self, host, port):
        self.connected = (host, port)

    def publish(self, topic, payload, retain=False):
        self.published.append((topic, payload, retain))

    def subscribe(self, topic):
        self.subscribed.append(topic)

    def loop_start(self):
        self.loop_started = True

    def loop_stop(self):
        self.loop_stopped = True

    def disconnect(self):
        self.disconnected = True


class FakeNabdClient:
    def __init__(self):
        self.commands = []

    async def sleep(self):
        self.commands.append("sleep")

    async def wakeup(self):
        self.commands.append("wakeup")

    async def set_volume(self, volume):
        self.commands.append(("volume", volume))
        return FakeNabdResponse({"volume": volume})

    async def set_muted(self, muted):
        self.commands.append(("mute", muted))
        return FakeNabdResponse({"muted": muted})


class FakeNabdResponse:
    def __init__(self, packet):
        self.packet = packet


class FakeMessage:
    def __init__(self, topic):
        self.topic = topic


class TestNabHomeAssistantd(unittest.IsolatedAsyncioTestCase):
    async def test_start_publishes_discovery_and_subscribes_commands(self):
        mqtt_client = FakeMqttClient()
        service = NabHomeAssistantd(
            config=HomeAssistantConfig(enabled=True),
            mqtt_client=mqtt_client,
        )

        await service._start_mqtt()

        self.assertEqual(mqtt_client.connected, ("homeassistant.local", 1883))
        self.assertIn("pynab/command/sleep", mqtt_client.subscribed)
        self.assertIn("pynab/command/wakeup", mqtt_client.subscribed)
        self.assertIn("pynab/command/volume", mqtt_client.subscribed)
        self.assertIn("pynab/command/mute", mqtt_client.subscribed)
        published_topics = [call[0] for call in mqtt_client.published]
        self.assertIn(
            "homeassistant/sensor/pynab/state/config", published_topics
        )
        self.assertIn(
            "homeassistant/number/pynab/volume/config", published_topics
        )
        self.assertIn(
            "homeassistant/switch/pynab/mute/config", published_topics
        )
        self.assertIn("pynab/availability", published_topics)
        self.assertTrue(mqtt_client.loop_started)

    async def test_state_packet_publishes_state(self):
        mqtt_client = FakeMqttClient()
        service = NabHomeAssistantd(
            config=HomeAssistantConfig(enabled=True),
            mqtt_client=mqtt_client,
        )

        await service.process_nabd_packet({"type": "state", "state": "idle"})

        self.assertIn(("pynab/state", "idle", True), mqtt_client.published)

    async def test_mqtt_commands_call_nabd(self):
        mqtt_client = FakeMqttClient()
        nabd_client = FakeNabdClient()
        service = NabHomeAssistantd(
            config=HomeAssistantConfig(enabled=True),
            mqtt_client=mqtt_client,
            nabd_client=nabd_client,
        )

        await service._run_command("sleep")
        await service._run_command("wakeup")
        await service._run_command("volume", b"35")
        await service._run_command("mute", b"ON")

        self.assertEqual(
            nabd_client.commands,
            ["sleep", "wakeup", ("volume", 35), ("mute", True)],
        )
        self.assertIn(("pynab/volume", "35", True), mqtt_client.published)
        self.assertIn(("pynab/mute", "ON", True), mqtt_client.published)


if __name__ == "__main__":
    unittest.main()

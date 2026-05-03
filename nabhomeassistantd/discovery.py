import json
from dataclasses import dataclass
from typing import Iterable

from .config import HomeAssistantConfig


@dataclass(frozen=True)
class MqttPublish:
    topic: str
    payload: str
    retain: bool = True


class HomeAssistantDiscovery:
    def __init__(self, config: HomeAssistantConfig):
        self.config = config

    @property
    def availability_topic(self) -> str:
        return f"{self.config.topic_prefix}/availability"

    @property
    def state_topic(self) -> str:
        return f"{self.config.topic_prefix}/state"

    @property
    def volume_state_topic(self) -> str:
        return f"{self.config.topic_prefix}/volume"

    @property
    def mute_state_topic(self) -> str:
        return f"{self.config.topic_prefix}/mute"

    @property
    def sleep_command_topic(self) -> str:
        return f"{self.config.topic_prefix}/command/sleep"

    @property
    def wakeup_command_topic(self) -> str:
        return f"{self.config.topic_prefix}/command/wakeup"

    @property
    def volume_command_topic(self) -> str:
        return f"{self.config.topic_prefix}/command/volume"

    @property
    def mute_command_topic(self) -> str:
        return f"{self.config.topic_prefix}/command/mute"

    def command_topics(self) -> list[str]:
        return [
            self.sleep_command_topic,
            self.wakeup_command_topic,
            self.volume_command_topic,
            self.mute_command_topic,
        ]

    def discovery_messages(self) -> Iterable[MqttPublish]:
        yield self._sensor_state()
        yield self._button("sleep", "Sleep", self.sleep_command_topic)
        yield self._button("wakeup", "Wake up", self.wakeup_command_topic)
        yield self._number_volume()
        yield self._switch_mute()

    def online_message(self) -> MqttPublish:
        return MqttPublish(self.availability_topic, "online")

    def offline_message(self) -> MqttPublish:
        return MqttPublish(self.availability_topic, "offline")

    def state_message(self, state: str) -> MqttPublish:
        return MqttPublish(self.state_topic, state, retain=True)

    def volume_message(self, volume: int) -> MqttPublish:
        return MqttPublish(self.volume_state_topic, str(volume), retain=True)

    def mute_message(self, muted: bool) -> MqttPublish:
        return MqttPublish(
            self.mute_state_topic, "ON" if muted else "OFF", retain=True
        )

    def _sensor_state(self) -> MqttPublish:
        payload = self._base_payload("state", "State")
        payload["state_topic"] = self.state_topic
        payload["icon"] = "mdi:rabbit"
        return self._discovery_publish("sensor", "state", payload)

    def _button(
        self, object_id: str, name: str, command_topic: str
    ) -> MqttPublish:
        payload = self._base_payload(object_id, name)
        payload["command_topic"] = command_topic
        payload["payload_press"] = "PRESS"
        return self._discovery_publish("button", object_id, payload)

    def _number_volume(self) -> MqttPublish:
        payload = self._base_payload("volume", "Volume")
        payload["state_topic"] = self.volume_state_topic
        payload["command_topic"] = self.volume_command_topic
        payload["min"] = 0
        payload["max"] = 100
        payload["step"] = 1
        payload["mode"] = "slider"
        payload["icon"] = "mdi:volume-high"
        return self._discovery_publish("number", "volume", payload)

    def _switch_mute(self) -> MqttPublish:
        payload = self._base_payload("mute", "Mute")
        payload["state_topic"] = self.mute_state_topic
        payload["command_topic"] = self.mute_command_topic
        payload["payload_on"] = "ON"
        payload["payload_off"] = "OFF"
        payload["icon"] = "mdi:volume-mute"
        return self._discovery_publish("switch", "mute", payload)

    def _base_payload(self, object_id: str, name: str) -> dict:
        return {
            "name": name,
            "unique_id": f"{self.config.topic_prefix}_{object_id}",
            "availability_topic": self.availability_topic,
            "device": {
                "identifiers": [self.config.topic_prefix],
                "name": self.config.device_name,
                "manufacturer": "Pynab",
                "model": "Nabaztag",
            },
        }

    def _discovery_publish(
        self, component: str, object_id: str, payload: dict
    ) -> MqttPublish:
        topic = (
            f"{self.config.discovery_prefix}/{component}/"
            f"{self.config.topic_prefix}/{object_id}/config"
        )
        return MqttPublish(topic, json.dumps(payload, sort_keys=True))

from dataclasses import dataclass


@dataclass(frozen=True)
class HomeAssistantConfig:
    enabled: bool = False
    mqtt_host: str = "homeassistant.local"
    mqtt_port: int = 1883
    mqtt_username: str = ""
    mqtt_password: str = ""
    device_name: str = "Pynab"
    discovery_prefix: str = "homeassistant"
    topic_prefix: str = "pynab"

    @classmethod
    def load(cls) -> "HomeAssistantConfig":
        from .models import Config

        record = Config.load()
        return cls(
            enabled=record.enabled,
            mqtt_host=record.mqtt_host,
            mqtt_port=record.mqtt_port,
            mqtt_username=record.mqtt_username,
            mqtt_password=record.mqtt_password,
            device_name=record.device_name,
            discovery_prefix=record.discovery_prefix,
            topic_prefix=record.topic_prefix,
        )

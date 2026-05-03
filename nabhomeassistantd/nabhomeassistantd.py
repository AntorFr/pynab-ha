import asyncio
import importlib
import logging
from typing import Any, Optional

from asgiref.sync import sync_to_async

from nabcommon.nabservice import NabService
from nabcommon.typing import NabdPacket

from .config import HomeAssistantConfig
from .discovery import HomeAssistantDiscovery
from .nabd_client import NabdClient


class NabHomeAssistantd(NabService):
    DAEMON_PIDFILE = "/run/nabhomeassistantd.pid"

    def __init__(
        self,
        config: Optional[HomeAssistantConfig] = None,
        mqtt_client: Any | None = None,
        nabd_client: NabdClient | None = None,
    ):
        super().__init__()
        self.config = config or HomeAssistantConfig.load()
        self.discovery = HomeAssistantDiscovery(self.config)
        self.mqtt_client = mqtt_client
        self.nabd_client = nabd_client or NabdClient()
        self.mqtt_started = False

    async def reload_config(self):
        new_config = await sync_to_async(HomeAssistantConfig.load)()
        if new_config == self.config:
            return
        await self._stop_mqtt()
        self.config = new_config
        self.discovery = HomeAssistantDiscovery(self.config)
        if self.config.enabled:
            await self._start_mqtt()

    async def process_nabd_packet(self, packet: NabdPacket) -> None:
        if packet["type"] == "state":
            await self._publish(self.discovery.state_message(packet["state"]))

    def start_service_loop(self, loop):
        if not self.config.enabled:
            return None
        return loop.create_task(self._start_mqtt())

    async def stop_service_loop(self) -> None:
        self.running = False
        await self._stop_mqtt()

    async def _start_mqtt(self) -> None:
        if self.mqtt_started:
            return
        client = self._mqtt_client()
        client.on_message = self._on_mqtt_message
        client.will_set(
            self.discovery.availability_topic, "offline", retain=True
        )
        if self.config.mqtt_username:
            client.username_pw_set(
                self.config.mqtt_username, self.config.mqtt_password
            )
        client.connect(self.config.mqtt_host, self.config.mqtt_port)
        client.loop_start()
        for message in self.discovery.discovery_messages():
            await self._publish(message)
        for topic in self.discovery.command_topics():
            client.subscribe(topic)
        await self._publish(self.discovery.online_message())
        self.mqtt_started = True

    async def _stop_mqtt(self) -> None:
        if self.mqtt_client is None or not self.mqtt_started:
            return
        await self._publish(self.discovery.offline_message())
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
        self.mqtt_started = False

    async def _publish(self, message) -> None:
        if not self.config.enabled or self.mqtt_client is None:
            return
        self.mqtt_client.publish(
            message.topic, message.payload, retain=message.retain
        )

    def _mqtt_client(self):
        if self.mqtt_client is None:
            mqtt = importlib.import_module("paho.mqtt.client")

            self.mqtt_client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2
            )
        return self.mqtt_client

    def _on_mqtt_message(self, client, userdata, message) -> None:
        if self.loop is None:
            return
        topic = message.topic
        if topic == self.discovery.sleep_command_topic:
            coro = self._run_command("sleep", message.payload)
        elif topic == self.discovery.wakeup_command_topic:
            coro = self._run_command("wakeup", message.payload)
        elif topic == self.discovery.volume_command_topic:
            coro = self._run_command("volume", message.payload)
        elif topic == self.discovery.mute_command_topic:
            coro = self._run_command("mute", message.payload)
        else:
            return
        asyncio.run_coroutine_threadsafe(coro, self.loop)

    async def _run_command(self, command: str, payload: bytes = b"") -> None:
        try:
            if command == "sleep":
                await self.nabd_client.sleep()
            elif command == "wakeup":
                await self.nabd_client.wakeup()
            elif command == "volume":
                volume = max(0, min(100, int(payload.decode("utf8"))))
                response = await self.nabd_client.set_volume(volume)
                reported = response.packet.get("volume", volume)
                await self._publish(self.discovery.volume_message(reported))
            elif command == "mute":
                muted = payload.decode("utf8").upper() == "ON"
                response = await self.nabd_client.set_muted(muted)
                reported = response.packet.get("muted", muted)
                await self._publish(self.discovery.mute_message(reported))
        except Exception:
            logging.exception("Unable to run Home Assistant command %s", command)


if __name__ == "__main__":
    import sys

    NabHomeAssistantd.main(sys.argv[1:])

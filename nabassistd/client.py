import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Protocol

from .audio import AudioFormat
from .processor import AssistWakeWordEvent


class AssistClient(Protocol):
    async def start_session(self, event: AssistWakeWordEvent) -> None:
        ...

    async def send_audio(self, pcm: bytes) -> None:
        ...

    async def end_session(self) -> None:
        ...

    async def ping(self, timeout: float = 2.0) -> bool:
        ...

    async def read_response_audio(self) -> bytes:
        ...

    async def disconnect(self) -> None:
        ...


class WyomingAsyncClient(Protocol):
    async def connect(self) -> None:
        ...

    async def disconnect(self) -> None:
        ...

    async def write_event(self, event) -> None:
        ...

    async def read_event(self):
        ...


@dataclass
class WyomingEvent:
    type: str
    data: Dict[str, Any] = field(default_factory=dict)
    payload: Optional[bytes] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.type, "data": self.data}


class WyomingAssistClient:
    def __init__(
        self,
        host: str,
        port: int,
        satellite_name: str,
        audio_format: AudioFormat = AudioFormat(),
        client: Optional[WyomingAsyncClient] = None,
    ):
        self.host = host
        self.port = port
        self.satellite_name = satellite_name
        self.audio_format = audio_format
        self.client = client
        self.connected = False

    async def start_session(self, event: AssistWakeWordEvent) -> None:
        await self._ensure_connected()

        assert self.client is not None
        await self.client.write_event(
            WyomingEvent(
                type="run-pipeline",
                data={
                    "start_stage": "asr",
                    "end_stage": "tts",
                    "restart_on_end": False,
                    "wake_word_name": event.result.name,
                },
            )
        )
        await self.client.write_event(
            WyomingEvent(
                type="audio-start",
                data=self._audio_format_data(),
            )
        )

    async def send_audio(self, pcm: bytes) -> None:
        if not pcm:
            return
        await self._ensure_connected()

        assert self.client is not None
        await self.client.write_event(
            WyomingEvent(
                type="audio-chunk",
                data=self._audio_format_data(),
                payload=pcm,
            )
        )

    async def end_session(self) -> None:
        await self._ensure_connected()

        assert self.client is not None
        await self.client.write_event(WyomingEvent(type="audio-stop"))

    async def ping(self, timeout: float = 2.0) -> bool:
        await self._ensure_connected()

        assert self.client is not None
        await self.client.write_event(
            WyomingEvent(type="ping", data={"text": self.satellite_name})
        )
        event = await asyncio.wait_for(self.client.read_event(), timeout)
        return (
            event is not None
            and event.type == "pong"
            and event.data.get("text") == self.satellite_name
        )

    async def read_response_audio(self) -> bytes:
        await self._ensure_connected()

        assert self.client is not None
        chunks: list[bytes] = []
        while True:
            event = await self.client.read_event()
            if event is None:
                break
            if event.type == "audio-chunk":
                chunks.append(event.payload or b"")
            elif event.type == "audio-stop":
                break
        return b"".join(chunks)

    async def disconnect(self) -> None:
        if self.client is not None and self.connected:
            await self.client.disconnect()
        self.connected = False

    async def _ensure_connected(self) -> None:
        if self.client is None:
            from wyoming.client import AsyncTcpClient

            self.client = AsyncTcpClient(self.host, self.port)
        if not self.connected:
            await self.client.connect()
            self.connected = True

    def _audio_format_data(self) -> Dict[str, Any]:
        return {
            "rate": self.audio_format.sample_rate,
            "width": self.audio_format.sample_width,
            "channels": self.audio_format.channels,
            "timestamp": None,
        }

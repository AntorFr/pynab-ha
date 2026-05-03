import asyncio
import json
from dataclasses import dataclass
from typing import Any

from nabcommon.nabservice import NabService


@dataclass(frozen=True)
class NabdResponse:
    status: str
    packet: dict[str, Any]


class NabdClient:
    def __init__(
        self,
        host: str = NabService.HOST,
        port: int = NabService.PORT_NUMBER,
        timeout: float = 2.0,
    ):
        self.host = host
        self.port = port
        self.timeout = timeout

    async def send(self, packet: dict[str, Any]) -> NabdResponse:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port), self.timeout
        )
        try:
            writer.write((json.dumps(packet) + "\r\n").encode("utf8"))
            await writer.drain()
            request_id = packet.get("request_id")
            while True:
                line = await asyncio.wait_for(
                    reader.readline(), self.timeout
                )
                if not line:
                    raise RuntimeError("nabd closed the connection")
                response = json.loads(line.decode("utf8"))
                if response.get("type") != "response":
                    continue
                if request_id and response.get("request_id") != request_id:
                    continue
                return NabdResponse(response.get("status", ""), response)
        finally:
            writer.close()
            await writer.wait_closed()

    async def sleep(self) -> NabdResponse:
        return await self.send(
            {"type": "sleep", "request_id": "ha_sleep"}
        )

    async def wakeup(self) -> NabdResponse:
        return await self.send(
            {"type": "wakeup", "request_id": "ha_wakeup"}
        )

    async def set_volume(self, volume: int) -> NabdResponse:
        return await self.send(
            {
                "type": "volume",
                "level": volume,
                "request_id": "ha_volume",
            }
        )

    async def set_muted(self, muted: bool) -> NabdResponse:
        return await self.send(
            {"type": "mute", "muted": muted, "request_id": "ha_mute"}
        )

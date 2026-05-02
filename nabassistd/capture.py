import asyncio
from dataclasses import dataclass
from typing import Optional

from nabd.sound import Sound


@dataclass(frozen=True)
class AudioChunk:
    pcm: bytes
    finalize: bool = False


class AssistAudioCapture:
    def __init__(self, sound: Sound):
        self.sound = sound
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._queue: asyncio.Queue[AudioChunk] = asyncio.Queue()
        self._running = False

    async def start(self) -> None:
        if self._running:
            return
        self._loop = asyncio.get_running_loop()
        self._running = True
        await self.sound.start_recording(self._recording_callback)

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        await self.sound.stop_recording()

    async def next_chunk(self) -> AudioChunk:
        return await self._queue.get()

    def _recording_callback(self, pcm: bytes, finalize: bool) -> None:
        if self._loop is None:
            return
        chunk = AudioChunk(pcm, finalize)
        self._loop.call_soon_threadsafe(self._queue.put_nowait, chunk)

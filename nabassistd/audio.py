from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class AudioFormat:
    sample_rate: int = 16000
    sample_width: int = 2
    channels: int = 1

    @property
    def bytes_per_second(self) -> int:
        return self.sample_rate * self.sample_width * self.channels


class AudioRingBuffer:
    def __init__(self, max_seconds: float, audio_format: AudioFormat):
        if max_seconds <= 0:
            raise ValueError("max_seconds must be positive")
        self._max_bytes = int(max_seconds * audio_format.bytes_per_second)
        self._buffer = bytearray()

    def append(self, chunk: bytes) -> None:
        if not chunk:
            return
        self._buffer.extend(chunk)
        overflow = len(self._buffer) - self._max_bytes
        if overflow > 0:
            del self._buffer[:overflow]

    def clear(self) -> None:
        self._buffer.clear()

    def bytes(self) -> bytes:
        return bytes(self._buffer)


class FixedSizeChunker:
    def __init__(self, frame_size: int):
        if frame_size <= 0:
            raise ValueError("frame_size must be positive")
        self._frame_size = frame_size
        self._buffer = bytearray()

    def push(self, chunk: bytes) -> Iterable[bytes]:
        if chunk:
            self._buffer.extend(chunk)
        while len(self._buffer) >= self._frame_size:
            frame = bytes(self._buffer[: self._frame_size])
            del self._buffer[: self._frame_size]
            yield frame

    def clear(self) -> None:
        self._buffer.clear()

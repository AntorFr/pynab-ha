from dataclasses import dataclass
from typing import Protocol


class EngineUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True)
class WakeWordResult:
    name: str
    score: float
    engine: str


class WakeWordEngine(Protocol):
    def process_audio(self, pcm: bytes) -> WakeWordResult | None:
        ...

    def reset(self) -> None:
        ...

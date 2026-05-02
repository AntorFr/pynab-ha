from .base import WakeWordResult


class RemoteWakeWordEngine:
    ENGINE_NAME = "remote"

    def __init__(self, model_name: str):
        self.model_name = model_name

    def process_audio(self, pcm: bytes) -> WakeWordResult | None:
        return None

    def reset(self) -> None:
        pass

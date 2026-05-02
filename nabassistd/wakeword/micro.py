from nabassistd.audio import FixedSizeChunker

from .base import EngineUnavailableError, WakeWordResult


class MicroWakeWordEngine:
    ENGINE_NAME = "micro"
    FRAME_SIZE = 160 * 2

    def __init__(self, model_name: str, sensitivity: float):
        try:
            from pymicro_wakeword import (  # type: ignore
                MicroWakeWord,
                MicroWakeWordFeatures,
                Model,
            )
        except ImportError as exc:
            raise EngineUnavailableError(
                "pymicro-wakeword is not installed. Install "
                "requirements-assist.txt to enable the micro wake-word engine."
            ) from exc

        self.model_name = model_name
        self.sensitivity = sensitivity
        self._chunker = FixedSizeChunker(self.FRAME_SIZE)
        self._features = MicroWakeWordFeatures()
        self._model = MicroWakeWord.from_builtin(
            _resolve_builtin_model(Model, model_name)
        )

    def process_audio(self, pcm: bytes) -> WakeWordResult | None:
        for frame in self._chunker.push(pcm):
            for features in self._features.process_streaming(frame):
                if self._model.process_streaming(features):
                    return WakeWordResult(
                        self.model_name, 1.0, self.ENGINE_NAME
                    )
        return None

    def reset(self) -> None:
        self._chunker.clear()


def _resolve_builtin_model(model_cls, model_name: str):
    enum_name = model_name.upper().replace("-", "_")
    try:
        return getattr(model_cls, enum_name)
    except AttributeError:
        available = ", ".join(item.name.lower() for item in model_cls)
        raise ValueError(
            f"Unsupported pymicro-wakeword model '{model_name}'. "
            f"Available built-ins: {available}"
        ) from None

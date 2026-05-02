from .base import EngineUnavailableError, WakeWordResult


class OpenWakeWordEngine:
    ENGINE_NAME = "openwakeword"

    def __init__(self, model_name: str, sensitivity: float):
        try:
            from openwakeword.model import Model  # type: ignore
        except ImportError as exc:
            raise EngineUnavailableError(
                "openwakeword is not installed. Install the optional "
                "openWakeWord dependency to enable this engine."
            ) from exc

        self.model_name = model_name
        self.sensitivity = sensitivity
        self._model = Model(wakeword_models=[model_name])

    def process_audio(self, pcm: bytes) -> WakeWordResult | None:
        prediction = self._model.predict(pcm)
        score = _score_for_model(prediction, self.model_name)
        if score >= self.sensitivity:
            return WakeWordResult(self.model_name, score, self.ENGINE_NAME)
        return None

    def reset(self) -> None:
        if hasattr(self._model, "reset"):
            self._model.reset()


def _score_for_model(prediction, model_name: str) -> float:
    if isinstance(prediction, dict):
        if model_name in prediction:
            return float(prediction[model_name])
        if prediction:
            return float(max(prediction.values()))
    return 0.0

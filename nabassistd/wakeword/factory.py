from nabassistd.config import WakeWordConfig, WakeWordEngineName

from .base import WakeWordEngine


def create_wake_word_engine(config: WakeWordConfig) -> WakeWordEngine:
    if config.engine == WakeWordEngineName.MICRO:
        from .micro import MicroWakeWordEngine

        return MicroWakeWordEngine(config.model, config.sensitivity)
    if config.engine == WakeWordEngineName.OPENWAKEWORD:
        from .openwakeword import OpenWakeWordEngine

        return OpenWakeWordEngine(config.model, config.sensitivity)
    if config.engine == WakeWordEngineName.REMOTE:
        from .remote import RemoteWakeWordEngine

        return RemoteWakeWordEngine(config.model)
    raise ValueError(f"Unsupported wake-word engine: {config.engine}")

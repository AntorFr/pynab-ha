import os
from dataclasses import dataclass
from enum import StrEnum


class WakeWordEngineName(StrEnum):
    MICRO = "micro"
    OPENWAKEWORD = "openwakeword"
    REMOTE = "remote"


@dataclass(frozen=True)
class WakeWordConfig:
    engine: WakeWordEngineName = WakeWordEngineName.MICRO
    model: str = "okay_nabu"
    sensitivity: float = 0.5
    pre_roll_seconds: float = 1.0
    fallback_to_remote: bool = False


@dataclass(frozen=True)
class AssistConfig:
    enabled: bool = False
    satellite_name: str = "Pynab"
    wyoming_host: str = "homeassistant.local"
    wyoming_port: int = 10300
    wake_word: WakeWordConfig = WakeWordConfig()

    @classmethod
    def load(cls) -> "AssistConfig":
        from .models import Config

        record = Config.load()
        return cls(
            enabled=record.enabled,
            satellite_name=record.satellite_name,
            wyoming_host=record.wyoming_host,
            wyoming_port=record.wyoming_port,
            wake_word=WakeWordConfig(
                engine=WakeWordEngineName(record.wake_word_engine),
                model=record.wake_word_model,
                sensitivity=record.wake_word_sensitivity,
                pre_roll_seconds=record.pre_roll_seconds,
                fallback_to_remote=record.fallback_to_remote,
            ),
        )

    @classmethod
    def from_env(cls) -> "AssistConfig":
        return cls(
            enabled=_bool_env("PYNAB_ASSIST_ENABLED", False),
            satellite_name=os.getenv("PYNAB_ASSIST_NAME", "Pynab"),
            wyoming_host=os.getenv(
                "PYNAB_ASSIST_WYOMING_HOST", "homeassistant.local"
            ),
            wyoming_port=int(os.getenv("PYNAB_ASSIST_WYOMING_PORT", "10300")),
            wake_word=WakeWordConfig(
                engine=WakeWordEngineName(
                    os.getenv("PYNAB_ASSIST_WAKE_ENGINE", "micro")
                ),
                model=os.getenv("PYNAB_ASSIST_WAKE_MODEL", "okay_nabu"),
                sensitivity=float(
                    os.getenv("PYNAB_ASSIST_WAKE_SENSITIVITY", "0.5")
                ),
                pre_roll_seconds=float(
                    os.getenv("PYNAB_ASSIST_PRE_ROLL_SECONDS", "1.0")
                ),
                fallback_to_remote=_bool_env(
                    "PYNAB_ASSIST_WAKE_FALLBACK_REMOTE", False
                ),
            ),
        )


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}

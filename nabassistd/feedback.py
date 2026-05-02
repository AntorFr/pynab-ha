import json
import logging
from enum import StrEnum
from typing import Any, Callable, Protocol

from nabd.sound import Sound


class AssistFeedbackState(StrEnum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    ERROR = "error"


class AssistFeedback(Protocol):
    async def set_state(self, state: AssistFeedbackState) -> None:
        pass


class FeedbackWriter(Protocol):
    def write(self, data: bytes) -> object:
        pass


class NoopAssistFeedback:
    async def set_state(self, state: AssistFeedbackState) -> None:
        pass


class NabdAssistFeedback:
    INFO_ID = "nabassistd"

    def __init__(
        self,
        writer_provider: Callable[[], FeedbackWriter | None],
        sound: Sound | None = None,
    ):
        self.writer_provider = writer_provider
        self.sound = sound

    async def set_state(self, state: AssistFeedbackState) -> None:
        if state == AssistFeedbackState.IDLE:
            self._send_info(None)
            return

        self._send_info(_animation_for_state(state))
        if state == AssistFeedbackState.ERROR and self.sound is not None:
            await self.sound.play_list(["asr/failed/*.mp3"], False)

    def _send_info(self, animation: dict | None) -> None:
        writer = self.writer_provider()
        if writer is None:
            return

        packet: dict[str, Any] = {
            "type": "info",
            "info_id": self.INFO_ID,
        }
        if animation is not None:
            packet["animation"] = animation
        try:
            writer.write((json.dumps(packet) + "\r\n").encode("utf8"))
        except Exception:
            logging.exception("Unable to send Assist feedback to nabd")


def _animation_for_state(state: AssistFeedbackState) -> dict:
    if state == AssistFeedbackState.LISTENING:
        return _pulse("00a6ff")
    if state == AssistFeedbackState.THINKING:
        return _scan("ffbf00")
    if state == AssistFeedbackState.SPEAKING:
        return _pulse("2fd36b")
    if state == AssistFeedbackState.ERROR:
        return _pulse("ff0000")
    return _off()


def _pulse(color: str) -> dict:
    return {
        "tempo": 12,
        "colors": [
            {"left": "", "center": color, "right": ""},
            {"left": color, "center": color, "right": color},
            {"left": "", "center": color, "right": ""},
            {"left": "", "center": "", "right": ""},
        ],
    }


def _scan(color: str) -> dict:
    return {
        "tempo": 8,
        "colors": [
            {"left": color, "center": "", "right": ""},
            {"left": "", "center": color, "right": ""},
            {"left": "", "center": "", "right": color},
            {"left": "", "center": color, "right": ""},
        ],
    }


def _off() -> dict:
    return {
        "tempo": 10,
        "colors": [{"left": "", "center": "", "right": ""}],
    }

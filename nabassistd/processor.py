from dataclasses import dataclass
from typing import Optional

from .audio import AudioFormat, AudioRingBuffer
from .wakeword import WakeWordEngine, WakeWordResult


@dataclass(frozen=True)
class AssistWakeWordEvent:
    result: WakeWordResult
    pre_roll_audio: bytes


class AssistAudioProcessor:
    def __init__(
        self,
        wake_word_engine: WakeWordEngine,
        pre_roll_seconds: float,
        audio_format: AudioFormat = AudioFormat(),
    ):
        self.audio_format = audio_format
        self.wake_word_engine = wake_word_engine
        self.pre_roll = AudioRingBuffer(pre_roll_seconds, audio_format)

    def process_audio(self, pcm: bytes) -> Optional[AssistWakeWordEvent]:
        self.pre_roll.append(pcm)
        result = self.wake_word_engine.process_audio(pcm)
        if result is None:
            return None
        return AssistWakeWordEvent(result, self.pre_roll.bytes())

    def reset(self) -> None:
        self.pre_roll.clear()
        self.wake_word_engine.reset()

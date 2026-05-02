import os
import tempfile
import wave
from typing import Protocol

from nabd.sound import Sound

from .audio import AudioFormat


class AssistAudioPlayer(Protocol):
    async def play_pcm(self, pcm: bytes, audio_format: AudioFormat) -> None:
        ...


class WavAssistAudioPlayer:
    def __init__(self, sound: Sound):
        self.sound = sound

    async def play_pcm(self, pcm: bytes, audio_format: AudioFormat) -> None:
        if not pcm:
            return

        path = _write_temp_wav(pcm, audio_format)
        try:
            await self.sound.start_playing_preloaded(path)
            await self.sound.wait_until_done()
        finally:
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass


def _write_temp_wav(pcm: bytes, audio_format: AudioFormat) -> str:
    with tempfile.NamedTemporaryFile(
        prefix="pynab-assist-", suffix=".wav", delete=False
    ) as file:
        path = file.name

    with wave.open(path, "wb") as wav_file:
        wav_file.setnchannels(audio_format.channels)
        wav_file.setsampwidth(audio_format.sample_width)
        wav_file.setframerate(audio_format.sample_rate)
        wav_file.writeframes(pcm)

    return path

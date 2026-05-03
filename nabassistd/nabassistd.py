import asyncio
import logging
from typing import Optional

from asgiref.sync import sync_to_async

from nabcommon.nabservice import NabService
from nabcommon.typing import NabdPacket
from nabd.sound import Sound

from .client import WyomingAssistClient
from .config import AssistConfig
from .capture import AssistAudioCapture
from .feedback import NabdAssistFeedback
from .playback import WavAssistAudioPlayer
from .pipeline import AssistPipeline
from .processor import AssistAudioProcessor
from .wakeword import create_wake_word_engine


class NabAssistd(NabService):
    DAEMON_PIDFILE = "/run/nabassistd.pid"
    ASSIST_ERROR_RETRY_INITIAL_SECONDS = 1.0
    ASSIST_ERROR_RETRY_MAX_SECONDS = 30.0

    def __init__(
        self,
        config: Optional[AssistConfig] = None,
        sound: Optional[Sound] = None,
    ):
        super().__init__()
        self.config = config or AssistConfig.load()
        self.audio_processor: Optional[AssistAudioProcessor] = None
        self.pipeline: Optional[AssistPipeline] = None
        self.capture: Optional[AssistAudioCapture] = None
        self.sound = sound
        if self.config.enabled and self.sound is None:
            self.sound = _create_default_sound()
        if self.config.enabled:
            self._build_pipeline()

    async def reload_config(self):
        self.config = await sync_to_async(AssistConfig.load)()
        if self.config.enabled and self.sound is None:
            self.sound = _create_default_sound()
        if self.config.enabled:
            self._build_pipeline()
        else:
            self.audio_processor = None
            self.pipeline = None
            self.capture = None

    async def process_nabd_packet(self, packet: NabdPacket) -> None:
        if packet["type"] == "button_event":
            logging.debug("Assist fallback button event: %s", packet)

    def start_service_loop(self, loop):
        if self.config.enabled and self.capture is not None:
            return loop.create_task(self.assist_loop())
        return None

    async def stop_service_loop(self) -> None:
        self.running = False
        if self.capture is not None:
            await self.capture.stop()

    async def assist_loop(self) -> None:
        if self.capture is None or self.pipeline is None:
            return

        await self.capture.start()
        error_retry_seconds = self.ASSIST_ERROR_RETRY_INITIAL_SECONDS
        try:
            while self.running:
                chunk = await self.capture.next_chunk()
                try:
                    await self.pipeline.process_chunk(chunk)
                    error_retry_seconds = (
                        self.ASSIST_ERROR_RETRY_INITIAL_SECONDS
                    )
                except Exception:
                    logging.exception(
                        "Assist pipeline failed; retrying in %.1fs",
                        error_retry_seconds,
                    )
                    await self._sleep_before_retry(error_retry_seconds)
                    error_retry_seconds = min(
                        error_retry_seconds * 2,
                        self.ASSIST_ERROR_RETRY_MAX_SECONDS,
                    )
        finally:
            await self.capture.stop()

    async def _sleep_before_retry(self, delay: float) -> None:
        if self.running:
            await asyncio.sleep(delay)

    def _build_pipeline(self) -> None:
        self.audio_processor = AssistAudioProcessor(
            create_wake_word_engine(self.config.wake_word),
            self.config.wake_word.pre_roll_seconds,
        )
        assist_client = WyomingAssistClient(
            self.config.wyoming_host,
            self.config.wyoming_port,
            self.config.satellite_name,
        )
        audio_player = None
        if self.sound is not None:
            audio_player = WavAssistAudioPlayer(self.sound)
            self.capture = AssistAudioCapture(self.sound)
        self.pipeline = AssistPipeline(
            self.audio_processor,
            assist_client,
            audio_player=audio_player,
            feedback=NabdAssistFeedback(lambda: self.writer, self.sound),
        )


def _create_default_sound() -> Sound:
    from nabd.nabio_hw import NabIOHW
    from nabd.sound_alsa import SoundAlsa

    return SoundAlsa(NabIOHW.detect_model())


if __name__ == "__main__":
    import sys

    NabAssistd.main(sys.argv[1:])

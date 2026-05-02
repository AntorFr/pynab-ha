import logging

from .capture import AudioChunk
from .client import AssistClient
from .feedback import AssistFeedback, AssistFeedbackState, NoopAssistFeedback
from .playback import AssistAudioPlayer
from .processor import AssistAudioProcessor


class AssistPipeline:
    def __init__(
        self,
        audio_processor: AssistAudioProcessor,
        assist_client: AssistClient,
        audio_player: AssistAudioPlayer | None = None,
        feedback: AssistFeedback | None = None,
    ):
        self.audio_processor = audio_processor
        self.assist_client = assist_client
        self.audio_player = audio_player
        self.feedback = feedback or NoopAssistFeedback()
        self.streaming = False

    async def process_chunk(self, chunk: AudioChunk) -> None:
        try:
            await self._process_chunk(chunk)
        except Exception:
            self.streaming = False
            self.audio_processor.reset()
            try:
                await self.assist_client.disconnect()
            except Exception:
                logging.exception("Unable to disconnect Wyoming client")
            await self.feedback.set_state(AssistFeedbackState.ERROR)
            raise

    async def _process_chunk(self, chunk: AudioChunk) -> None:
        if self.streaming:
            if chunk.pcm:
                await self.assist_client.send_audio(chunk.pcm)
            if chunk.finalize:
                await self.feedback.set_state(AssistFeedbackState.THINKING)
                await self.assist_client.end_session()
                response_audio = await self.assist_client.read_response_audio()
                if self.audio_player is not None and response_audio:
                    await self.feedback.set_state(AssistFeedbackState.SPEAKING)
                    await self.audio_player.play_pcm(
                        response_audio, self.audio_processor.audio_format
                    )
                await self.feedback.set_state(AssistFeedbackState.IDLE)
                self.streaming = False
                self.audio_processor.reset()
            return

        if chunk.finalize:
            self.audio_processor.reset()
            await self.feedback.set_state(AssistFeedbackState.IDLE)
            return

        event = self.audio_processor.process_audio(chunk.pcm)
        if event is None:
            return

        await self.feedback.set_state(AssistFeedbackState.LISTENING)
        await self.assist_client.start_session(event)
        await self.assist_client.send_audio(event.pre_roll_audio)
        self.streaming = True

import unittest

from nabassistd.audio import AudioFormat
from nabassistd.capture import AudioChunk
from nabassistd.feedback import AssistFeedbackState
from nabassistd.pipeline import AssistPipeline
from nabassistd.processor import AssistAudioProcessor
from nabassistd.wakeword import WakeWordResult


class FakeWakeWordEngine:
    def __init__(self):
        self.reset_called = False

    def process_audio(self, pcm):
        if b"wake" in pcm:
            return WakeWordResult("okay_nabu", 0.9, "fake")
        return None

    def reset(self):
        self.reset_called = True


class FakeAssistClient:
    def __init__(self):
        self.calls = []
        self.response_audio = b""

    async def start_session(self, event):
        self.calls.append(("start", event.result.name))

    async def send_audio(self, pcm):
        self.calls.append(("audio", pcm))

    async def end_session(self):
        self.calls.append(("end", None))

    async def read_response_audio(self):
        self.calls.append(("read_response", None))
        return self.response_audio

    async def disconnect(self):
        self.calls.append(("disconnect", None))


class FailingAssistClient(FakeAssistClient):
    async def start_session(self, event):
        raise RuntimeError("boom")


class FakeAudioPlayer:
    def __init__(self):
        self.played = []

    async def play_pcm(self, pcm, audio_format):
        self.played.append((pcm, audio_format))


class FakeFeedback:
    def __init__(self):
        self.states = []

    async def set_state(self, state):
        self.states.append(state)


class TestAssistPipeline(unittest.IsolatedAsyncioTestCase):
    async def test_starts_session_and_sends_pre_roll_on_wake_word(self):
        processor = AssistAudioProcessor(
            FakeWakeWordEngine(),
            pre_roll_seconds=1.0,
            audio_format=AudioFormat(sample_rate=20, sample_width=1),
        )
        client = FakeAssistClient()
        feedback = FakeFeedback()
        pipeline = AssistPipeline(processor, client, feedback=feedback)

        await pipeline.process_chunk(AudioChunk(b"hello "))
        await pipeline.process_chunk(AudioChunk(b"wake"))

        self.assertTrue(pipeline.streaming)
        self.assertEqual(
            client.calls,
            [
                ("start", "okay_nabu"),
                ("audio", b"hello wake"),
            ],
        )
        self.assertEqual(feedback.states, [AssistFeedbackState.LISTENING])

    async def test_streams_audio_until_finalize(self):
        engine = FakeWakeWordEngine()
        processor = AssistAudioProcessor(
            engine,
            pre_roll_seconds=1.0,
            audio_format=AudioFormat(sample_rate=20, sample_width=1),
        )
        client = FakeAssistClient()
        feedback = FakeFeedback()
        pipeline = AssistPipeline(processor, client, feedback=feedback)

        await pipeline.process_chunk(AudioChunk(b"wake"))
        await pipeline.process_chunk(AudioChunk(b" turn on light"))
        await pipeline.process_chunk(AudioChunk(b"", finalize=True))

        self.assertFalse(pipeline.streaming)
        self.assertTrue(engine.reset_called)
        self.assertEqual(
            client.calls,
            [
                ("start", "okay_nabu"),
                ("audio", b"wake"),
                ("audio", b" turn on light"),
                ("end", None),
                ("read_response", None),
            ],
        )
        self.assertEqual(
            feedback.states,
            [
                AssistFeedbackState.LISTENING,
                AssistFeedbackState.THINKING,
                AssistFeedbackState.IDLE,
            ],
        )

    async def test_plays_response_audio_after_finalize(self):
        processor = AssistAudioProcessor(
            FakeWakeWordEngine(),
            pre_roll_seconds=1.0,
            audio_format=AudioFormat(sample_rate=16000, sample_width=2),
        )
        client = FakeAssistClient()
        client.response_audio = b"tts-pcm"
        player = FakeAudioPlayer()
        feedback = FakeFeedback()
        pipeline = AssistPipeline(
            processor, client, audio_player=player, feedback=feedback
        )

        await pipeline.process_chunk(AudioChunk(b"wake"))
        await pipeline.process_chunk(AudioChunk(b"", finalize=True))

        self.assertEqual(len(player.played), 1)
        self.assertEqual(player.played[0][0], b"tts-pcm")
        self.assertEqual(player.played[0][1].sample_rate, 16000)
        self.assertEqual(
            feedback.states,
            [
                AssistFeedbackState.LISTENING,
                AssistFeedbackState.THINKING,
                AssistFeedbackState.SPEAKING,
                AssistFeedbackState.IDLE,
            ],
        )

    async def test_reports_error_and_resets_on_client_failure(self):
        engine = FakeWakeWordEngine()
        processor = AssistAudioProcessor(
            engine,
            pre_roll_seconds=1.0,
            audio_format=AudioFormat(sample_rate=20, sample_width=1),
        )
        feedback = FakeFeedback()
        client = FailingAssistClient()
        pipeline = AssistPipeline(
            processor, client, feedback=feedback
        )

        with self.assertRaises(RuntimeError):
            await pipeline.process_chunk(AudioChunk(b"wake"))

        self.assertFalse(pipeline.streaming)
        self.assertTrue(engine.reset_called)
        self.assertEqual(
            feedback.states,
            [AssistFeedbackState.LISTENING, AssistFeedbackState.ERROR],
        )
        self.assertEqual(client.calls, [("disconnect", None)])


if __name__ == "__main__":
    unittest.main()

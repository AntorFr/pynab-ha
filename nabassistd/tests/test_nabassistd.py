import unittest

from nabassistd.capture import AudioChunk
from nabassistd.config import AssistConfig, WakeWordConfig, WakeWordEngineName
from nabassistd.nabassistd import NabAssistd
from nabd.sound import Sound


class FakeSound(Sound):
    async def start_recording(self, stream_cb):
        pass

    async def stop_recording(self):
        pass

    async def start_playing_preloaded(self, filename):
        pass

    async def wait_until_done(self, event=None):
        pass

    async def stop_playing(self):
        pass


class FakeCapture:
    def __init__(self):
        self.started = False
        self.stopped = False
        self.chunks = [AudioChunk(b"first"), AudioChunk(b"second")]

    async def start(self):
        self.started = True

    async def stop(self):
        self.stopped = True

    async def next_chunk(self):
        return self.chunks.pop(0)


class FailingOncePipeline:
    def __init__(self, service):
        self.service = service
        self.processed = []

    async def process_chunk(self, chunk):
        self.processed.append(chunk.pcm)
        if len(self.processed) == 1:
            raise RuntimeError("temporary failure")
        self.service.running = False


class TestNabAssistd(unittest.TestCase):
    def test_disabled_config_does_not_build_audio_pipeline(self):
        service = NabAssistd(config=AssistConfig(enabled=False))

        self.assertIsNone(service.audio_processor)
        self.assertIsNone(service.pipeline)
        self.assertIsNone(service.capture)

    def test_enabled_config_builds_capture_when_sound_is_available(self):
        service = NabAssistd(
            config=AssistConfig(
                enabled=True,
                wake_word=WakeWordConfig(engine=WakeWordEngineName.REMOTE),
            ),
            sound=FakeSound(),
        )

        self.assertIsNotNone(service.audio_processor)
        self.assertIsNotNone(service.pipeline)
        self.assertIsNotNone(service.capture)


class TestNabAssistdLoop(unittest.IsolatedAsyncioTestCase):
    async def test_assist_loop_retries_after_pipeline_error(self):
        service = NabAssistd(config=AssistConfig(enabled=False))
        service.ASSIST_ERROR_RETRY_INITIAL_SECONDS = 0
        service.capture = FakeCapture()
        service.pipeline = FailingOncePipeline(service)

        await service.assist_loop()

        self.assertTrue(service.capture.started)
        self.assertTrue(service.capture.stopped)
        self.assertEqual(
            service.pipeline.processed,
            [b"first", b"second"],
        )


if __name__ == "__main__":
    unittest.main()

import unittest

from nabassistd.config import WakeWordConfig, WakeWordEngineName
from nabassistd.processor import AssistAudioProcessor
from nabassistd.wakeword import WakeWordResult, create_wake_word_engine


class FakeWakeWordEngine:
    def __init__(self, trigger_after_bytes):
        self.trigger_after_bytes = trigger_after_bytes
        self.seen = 0
        self.reset_called = False

    def process_audio(self, pcm):
        self.seen += len(pcm)
        if self.seen >= self.trigger_after_bytes:
            return WakeWordResult("okay_nabu", 0.9, "fake")
        return None

    def reset(self):
        self.reset_called = True


class TestWakeWordFactory(unittest.TestCase):
    def test_remote_engine_can_be_created_without_optional_dependencies(self):
        engine = create_wake_word_engine(
            WakeWordConfig(engine=WakeWordEngineName.REMOTE)
        )

        self.assertIsNone(engine.process_audio(b"audio"))


class TestAssistAudioProcessor(unittest.TestCase):
    def test_returns_detection_with_pre_roll_audio(self):
        engine = FakeWakeWordEngine(trigger_after_bytes=6)
        processor = AssistAudioProcessor(engine, pre_roll_seconds=1.0)

        self.assertIsNone(processor.process_audio(b"12"))
        event = processor.process_audio(b"3456")

        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.result.name, "okay_nabu")
        self.assertEqual(event.pre_roll_audio, b"123456")

    def test_reset_clears_pre_roll_and_engine(self):
        engine = FakeWakeWordEngine(trigger_after_bytes=10)
        processor = AssistAudioProcessor(engine, pre_roll_seconds=1.0)

        processor.process_audio(b"1234")
        processor.reset()

        self.assertTrue(engine.reset_called)
        self.assertEqual(processor.pre_roll.bytes(), b"")


if __name__ == "__main__":
    unittest.main()

import json
import unittest

from nabassistd.feedback import AssistFeedbackState, NabdAssistFeedback


class FakeWriter:
    def __init__(self):
        self.writes = []

    def write(self, data):
        self.writes.append(json.loads(data.decode("utf8")))


class FakeSound:
    def __init__(self):
        self.played = []

    async def play_list(self, playlist, interrupt):
        self.played.append((playlist, interrupt))


class TestNabdAssistFeedback(unittest.IsolatedAsyncioTestCase):
    async def test_sends_state_animation(self):
        writer = FakeWriter()
        feedback = NabdAssistFeedback(lambda: writer)

        await feedback.set_state(AssistFeedbackState.LISTENING)

        self.assertEqual(len(writer.writes), 1)
        self.assertEqual(writer.writes[0]["type"], "info")
        self.assertEqual(writer.writes[0]["info_id"], "nabassistd")
        self.assertIn("animation", writer.writes[0])

    async def test_idle_clears_state_animation(self):
        writer = FakeWriter()
        feedback = NabdAssistFeedback(lambda: writer)

        await feedback.set_state(AssistFeedbackState.IDLE)

        self.assertEqual(
            writer.writes[0],
            {"type": "info", "info_id": "nabassistd"},
        )

    async def test_error_plays_existing_asr_failed_sound(self):
        writer = FakeWriter()
        sound = FakeSound()
        feedback = NabdAssistFeedback(lambda: writer, sound=sound)

        await feedback.set_state(AssistFeedbackState.ERROR)

        self.assertEqual(sound.played, [(["asr/failed/*.mp3"], False)])


if __name__ == "__main__":
    unittest.main()

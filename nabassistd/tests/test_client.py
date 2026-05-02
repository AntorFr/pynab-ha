import unittest

from nabassistd.audio import AudioFormat
from nabassistd.client import WyomingAssistClient
from nabassistd.processor import AssistWakeWordEvent
from nabassistd.wakeword import WakeWordResult


class FakeWyomingClient:
    def __init__(self, read_events=None):
        self.connected = False
        self.disconnected = False
        self.events = []
        self.read_events = list(read_events or [])

    async def connect(self):
        self.connected = True

    async def disconnect(self):
        self.disconnected = True

    async def write_event(self, event):
        self.events.append(event)

    async def read_event(self):
        if not self.read_events:
            return None
        return self.read_events.pop(0)


class TestWyomingAssistClient(unittest.IsolatedAsyncioTestCase):
    async def test_ping_returns_true_on_matching_pong(self):
        fake = FakeWyomingClient(
            [
                type(
                    "Event",
                    (),
                    {
                        "type": "pong",
                        "data": {"text": "Lapin"},
                        "payload": None,
                    },
                )()
            ]
        )
        client = WyomingAssistClient("ha.local", 10300, "Lapin", client=fake)

        self.assertTrue(await client.ping())
        self.assertEqual(fake.events[0].type, "ping")
        self.assertEqual(fake.events[0].data["text"], "Lapin")

    async def test_ping_returns_false_on_unexpected_response(self):
        fake = FakeWyomingClient(
            [
                type(
                    "Event",
                    (),
                    {
                        "type": "pong",
                        "data": {"text": "Other"},
                        "payload": None,
                    },
                )()
            ]
        )
        client = WyomingAssistClient("ha.local", 10300, "Lapin", client=fake)

        self.assertFalse(await client.ping())

    async def test_starts_pipeline_and_audio_stream(self):
        fake = FakeWyomingClient()
        client = WyomingAssistClient(
            "ha.local",
            10300,
            "Lapin",
            audio_format=AudioFormat(sample_rate=16000, sample_width=2),
            client=fake,
        )
        event = AssistWakeWordEvent(
            WakeWordResult("okay_nabu", 0.9, "micro"), b"pre"
        )

        await client.start_session(event)

        self.assertTrue(fake.connected)
        self.assertEqual(fake.events[0].type, "run-pipeline")
        self.assertEqual(fake.events[0].data["start_stage"], "asr")
        self.assertEqual(fake.events[0].data["end_stage"], "tts")
        self.assertEqual(fake.events[0].data["wake_word_name"], "okay_nabu")
        self.assertEqual(fake.events[1].type, "audio-start")
        self.assertEqual(fake.events[1].data["rate"], 16000)
        self.assertEqual(fake.events[1].data["width"], 2)
        self.assertEqual(fake.events[1].data["channels"], 1)

    async def test_sends_audio_chunks_and_stop(self):
        fake = FakeWyomingClient()
        client = WyomingAssistClient(
            "ha.local",
            10300,
            "Lapin",
            client=fake,
        )

        await client.send_audio(b"pcm")
        await client.end_session()

        self.assertEqual(fake.events[0].type, "audio-chunk")
        self.assertEqual(fake.events[0].payload, b"pcm")
        self.assertEqual(fake.events[1].type, "audio-stop")

    async def test_disconnects_underlying_client(self):
        fake = FakeWyomingClient()
        client = WyomingAssistClient("ha.local", 10300, "Lapin", client=fake)

        await client.send_audio(b"pcm")
        await client.disconnect()

        self.assertTrue(fake.disconnected)
        self.assertFalse(client.connected)

    async def test_reads_response_audio_until_audio_stop(self):
        fake = FakeWyomingClient(
            [
                type("Event", (), {"type": "audio-start", "payload": None})(),
                type("Event", (), {"type": "audio-chunk", "payload": b"one"})(),
                type("Event", (), {"type": "audio-chunk", "payload": b"two"})(),
                type("Event", (), {"type": "audio-stop", "payload": None})(),
            ]
        )
        client = WyomingAssistClient("ha.local", 10300, "Lapin", client=fake)

        audio = await client.read_response_audio()

        self.assertEqual(audio, b"onetwo")


if __name__ == "__main__":
    unittest.main()

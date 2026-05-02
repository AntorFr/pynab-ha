import asyncio
import unittest

from nabassistd.capture import AssistAudioCapture


class FakeSound:
    def __init__(self):
        self.callback = None
        self.started = False
        self.stopped = False

    async def start_recording(self, stream_cb):
        self.callback = stream_cb
        self.started = True

    async def stop_recording(self):
        self.stopped = True
        if self.callback:
            self.callback(b"", True)


class TestAssistAudioCapture(unittest.IsolatedAsyncioTestCase):
    async def test_queues_recorded_chunks(self):
        sound = FakeSound()
        capture = AssistAudioCapture(sound)

        await capture.start()
        assert sound.callback is not None
        sound.callback(b"pcm", False)
        chunk = await asyncio.wait_for(capture.next_chunk(), timeout=1)

        self.assertTrue(sound.started)
        self.assertEqual(chunk.pcm, b"pcm")
        self.assertFalse(chunk.finalize)

    async def test_stop_emits_finalize_chunk(self):
        sound = FakeSound()
        capture = AssistAudioCapture(sound)

        await capture.start()
        await capture.stop()
        chunk = await asyncio.wait_for(capture.next_chunk(), timeout=1)

        self.assertTrue(sound.stopped)
        self.assertEqual(chunk.pcm, b"")
        self.assertTrue(chunk.finalize)


if __name__ == "__main__":
    unittest.main()

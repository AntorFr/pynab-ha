import os
import unittest
import wave

from nabassistd.audio import AudioFormat
from nabassistd.playback import WavAssistAudioPlayer


class FakeSound:
    def __init__(self):
        self.played_path = None
        self.wav_info = None
        self.waited = False

    async def start_playing_preloaded(self, filename):
        self.played_path = filename
        with wave.open(filename, "rb") as wav_file:
            self.wav_info = (
                wav_file.getframerate(),
                wav_file.getsampwidth(),
                wav_file.getnchannels(),
                wav_file.readframes(wav_file.getnframes()),
            )

    async def wait_until_done(self, event=None):
        self.waited = True


class TestWavAssistAudioPlayer(unittest.IsolatedAsyncioTestCase):
    async def test_writes_pcm_to_temp_wav_and_plays_it(self):
        sound = FakeSound()
        player = WavAssistAudioPlayer(sound)

        await player.play_pcm(
            b"\x01\x00\x02\x00",
            AudioFormat(sample_rate=16000, sample_width=2, channels=1),
        )

        self.assertIsNotNone(sound.played_path)
        assert sound.played_path is not None
        self.assertFalse(os.path.exists(sound.played_path))
        self.assertTrue(sound.waited)
        self.assertEqual(sound.wav_info, (16000, 2, 1, b"\x01\x00\x02\x00"))

    async def test_ignores_empty_audio(self):
        sound = FakeSound()
        player = WavAssistAudioPlayer(sound)

        await player.play_pcm(b"", AudioFormat())

        self.assertIsNone(sound.played_path)


if __name__ == "__main__":
    unittest.main()

import unittest

from nabassistd.audio import AudioFormat, AudioRingBuffer, FixedSizeChunker


class TestAudioRingBuffer(unittest.TestCase):
    def test_keeps_only_configured_duration(self):
        audio_format = AudioFormat(sample_rate=10, sample_width=1, channels=1)
        ring = AudioRingBuffer(max_seconds=1.0, audio_format=audio_format)

        ring.append(b"12345")
        ring.append(b"67890")
        ring.append(b"abc")

        self.assertEqual(ring.bytes(), b"4567890abc")

    def test_ignores_empty_chunks(self):
        audio_format = AudioFormat(sample_rate=10, sample_width=1, channels=1)
        ring = AudioRingBuffer(max_seconds=1.0, audio_format=audio_format)

        ring.append(b"")

        self.assertEqual(ring.bytes(), b"")


class TestFixedSizeChunker(unittest.TestCase):
    def test_splits_across_pushes(self):
        chunker = FixedSizeChunker(frame_size=4)

        self.assertEqual(list(chunker.push(b"12")), [])
        self.assertEqual(list(chunker.push(b"3456789")), [b"1234", b"5678"])
        self.assertEqual(list(chunker.push(b"0ab")), [b"90ab"])


if __name__ == "__main__":
    unittest.main()

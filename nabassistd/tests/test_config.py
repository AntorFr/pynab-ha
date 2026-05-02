import os
import unittest
from unittest.mock import patch

from nabassistd.config import AssistConfig, WakeWordEngineName


class TestAssistConfig(unittest.TestCase):
    def test_defaults_to_micro_wake_word(self):
        with patch.dict(os.environ, {}, clear=True):
            config = AssistConfig.from_env()

        self.assertFalse(config.enabled)
        self.assertEqual(config.wake_word.engine, WakeWordEngineName.MICRO)
        self.assertEqual(config.wake_word.model, "okay_nabu")
        self.assertEqual(config.wake_word.sensitivity, 0.5)

    def test_reads_wake_word_config_from_env(self):
        with patch.dict(
            os.environ,
            {
                "PYNAB_ASSIST_ENABLED": "true",
                "PYNAB_ASSIST_NAME": "Lapin",
                "PYNAB_ASSIST_WAKE_ENGINE": "openwakeword",
                "PYNAB_ASSIST_WAKE_MODEL": "hey_jarvis",
                "PYNAB_ASSIST_WAKE_SENSITIVITY": "0.7",
                "PYNAB_ASSIST_PRE_ROLL_SECONDS": "1.5",
            },
            clear=True,
        ):
            config = AssistConfig.from_env()

        self.assertTrue(config.enabled)
        self.assertEqual(config.satellite_name, "Lapin")
        self.assertEqual(
            config.wake_word.engine, WakeWordEngineName.OPENWAKEWORD
        )
        self.assertEqual(config.wake_word.model, "hey_jarvis")
        self.assertEqual(config.wake_word.sensitivity, 0.7)
        self.assertEqual(config.wake_word.pre_roll_seconds, 1.5)


if __name__ == "__main__":
    unittest.main()

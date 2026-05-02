from django.core import validators
from django.db import models

from nabcommon import singleton_model


class Config(singleton_model.SingletonModel):
    WAKE_WORD_ENGINE_MICRO = "micro"
    WAKE_WORD_ENGINE_OPENWAKEWORD = "openwakeword"
    WAKE_WORD_ENGINE_REMOTE = "remote"

    WAKE_WORD_ENGINE_CHOICES = [
        (WAKE_WORD_ENGINE_MICRO, "pymicro-wakeword"),
        (WAKE_WORD_ENGINE_OPENWAKEWORD, "openWakeWord"),
        (WAKE_WORD_ENGINE_REMOTE, "Home Assistant"),
    ]

    enabled = models.BooleanField(default=False)
    satellite_name = models.TextField(default="Pynab")
    wyoming_host = models.TextField(default="homeassistant.local")
    wyoming_port = models.IntegerField(
        default=10300,
        validators=[
            validators.MinValueValidator(1),
            validators.MaxValueValidator(65535),
        ],
    )
    wake_word_engine = models.TextField(
        default=WAKE_WORD_ENGINE_MICRO,
        choices=WAKE_WORD_ENGINE_CHOICES,
    )
    wake_word_model = models.TextField(default="okay_nabu")
    wake_word_sensitivity = models.FloatField(
        default=0.5,
        validators=[
            validators.MinValueValidator(0.0),
            validators.MaxValueValidator(1.0),
        ],
    )
    pre_roll_seconds = models.FloatField(
        default=1.0,
        validators=[
            validators.MinValueValidator(0.1),
            validators.MaxValueValidator(5.0),
        ],
    )
    fallback_to_remote = models.BooleanField(default=False)

    class Meta:
        app_label = "nabassistd"

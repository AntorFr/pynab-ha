from django.core import validators
from django.db import models

from nabcommon import singleton_model


class Config(singleton_model.SingletonModel):
    enabled = models.BooleanField(default=False)
    mqtt_host = models.TextField(default="homeassistant.local")
    mqtt_port = models.IntegerField(
        default=1883,
        validators=[
            validators.MinValueValidator(1),
            validators.MaxValueValidator(65535),
        ],
    )
    mqtt_username = models.TextField(blank=True, default="")
    mqtt_password = models.TextField(blank=True, default="")
    device_name = models.TextField(default="Pynab")
    discovery_prefix = models.TextField(default="homeassistant")
    topic_prefix = models.TextField(default="pynab")

    class Meta:
        app_label = "nabhomeassistantd"

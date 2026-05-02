# Generated manually for the Assist Satellite configuration singleton.

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Config",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("enabled", models.BooleanField(default=False)),
                ("satellite_name", models.TextField(default="Pynab")),
                (
                    "wyoming_host",
                    models.TextField(default="homeassistant.local"),
                ),
                (
                    "wyoming_port",
                    models.IntegerField(
                        default=10300,
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(65535),
                        ],
                    ),
                ),
                (
                    "wake_word_engine",
                    models.TextField(
                        choices=[
                            ("micro", "pymicro-wakeword"),
                            ("openwakeword", "openWakeWord"),
                            ("remote", "Home Assistant"),
                        ],
                        default="micro",
                    ),
                ),
                ("wake_word_model", models.TextField(default="okay_nabu")),
                (
                    "wake_word_sensitivity",
                    models.FloatField(
                        default=0.5,
                        validators=[
                            django.core.validators.MinValueValidator(0.0),
                            django.core.validators.MaxValueValidator(1.0),
                        ],
                    ),
                ),
                (
                    "pre_roll_seconds",
                    models.FloatField(
                        default=1.0,
                        validators=[
                            django.core.validators.MinValueValidator(0.1),
                            django.core.validators.MaxValueValidator(5.0),
                        ],
                    ),
                ),
                ("fallback_to_remote", models.BooleanField(default=False)),
            ],
            options={
                "app_label": "nabassistd",
            },
        ),
    ]

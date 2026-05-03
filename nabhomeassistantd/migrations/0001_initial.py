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
                ("mqtt_host", models.TextField(default="homeassistant.local")),
                (
                    "mqtt_port",
                    models.IntegerField(
                        default=1883,
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(65535),
                        ],
                    ),
                ),
                ("mqtt_username", models.TextField(blank=True, default="")),
                ("mqtt_password", models.TextField(blank=True, default="")),
                ("device_name", models.TextField(default="Pynab")),
                (
                    "discovery_prefix",
                    models.TextField(default="homeassistant"),
                ),
                ("topic_prefix", models.TextField(default="pynab")),
            ],
        ),
    ]

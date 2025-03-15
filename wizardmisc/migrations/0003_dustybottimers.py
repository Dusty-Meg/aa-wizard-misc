# Generated by Django 4.0.10 on 2023-12-22 10:15

# Django
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("wizardmisc", "0002_dustybotcommands"),
    ]

    operations = [
        migrations.CreateModel(
            name="DustyBotTimers",
            fields=[
                (
                    "TimerId",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("SystemName", models.TextField()),
                ("BeltType", models.TextField()),
                ("RespawnTime", models.DateTimeField(blank=False, default=None, null=False)),
                ("ReportedTime", models.DateTimeField(blank=False, default=None, null=False)),
            ],
        ),
    ]
# Generated by Django 4.0.10 on 2023-08-29 13:36

# Django
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Settings",
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
                ("setting_id", models.CharField(max_length=500)),
                ("value", models.CharField(max_length=500)),
            ],
        ),
    ]

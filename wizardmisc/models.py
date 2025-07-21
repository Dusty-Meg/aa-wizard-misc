"""
App Models
Create your models in here
"""

# Django
from django.db import models


class Settings(models.Model):
    setting_id = models.CharField(max_length=500)
    value = models.CharField(max_length=500)


class DustyBotCommands(models.Model):
    key = models.TextField()
    message = models.TextField()


class DustyBotTimers(models.Model):
    TimerId = models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")
    SystemName = models.TextField()
    BeltType = models.TextField()
    RespawnTime = models.DateTimeField(blank=False, default=None, null=False)
    ReportedTime = models.DateTimeField(blank=False, default=None, null=False)

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

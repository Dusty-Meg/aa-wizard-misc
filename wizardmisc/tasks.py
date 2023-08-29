"""App Tasks"""

# Standard Library
import logging

# Third Party
import requests
from celery import shared_task

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter

from .app_settings import JABBERBOT_URL
from .models import Settings

logger = logging.getLogger(__name__)

# Create your tasks here


# Example Task
@shared_task
def blacklist_check():
    logger.debug("Checking s:")
    last_id, created = Settings.objects.get_or_create(
        setting_id="BlacklistLastId",
        defaults={"setting_id": "BlacklistLastId", "value": "0"},
    )

    if created:
        last_id = 0
    else:
        last_id = int(last_id.value)

    for character in EveCharacter.objects.filter(id__gt=last_id):
        try:
            logger.debug(f"Checking character: {character.character_name}")
            requests.get(f"{JABBERBOT_URL}/blacklist/{character.character_name}")
            last_id = character.id
        except Exception as error:
            logging.error(f"Error connecting to Jabber! {error}")

    Settings.objects.update_or_create(setting_id="BlacklistLastId", value=last_id)

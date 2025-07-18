"""App Tasks"""

# Standard Library
import json
import logging
import datetime

# Third Party
import requests
from celery import shared_task

# Django
from django.conf import settings

# Alliance Auth
from allianceauth.authentication.models import UserProfile
from allianceauth.eveonline.models import EveCharacter

from structures.models import Notification as StructuresNotification
from structures.models import Structure as StructuresStructure
from structuretimers.models import Timer as StructureTimersTimer

from .app_settings import HR_FORUM_WEBHOOK, JABBERBOT_URL
from .models import Settings

logger = logging.getLogger(__name__)

# Create your tasks here


def send_discord_message(body_dict, webhook):
    header = {"Content-Type": "application/json"}

    requests.post(url=webhook, data=json.dumps(body_dict), headers=header)


def get_full_class_name(obj):
    module = obj.__class__.__module__
    if module is None or module == str.__class__.__module__:
        return obj.__class__.__name__
    return module + "." + obj.__class__.__name__


@shared_task
def blacklist_check():
    settings_key = "BlacklistLastId"
    last_id, created = Settings.objects.get_or_create(
        setting_id=settings_key,
        defaults={"setting_id": settings_key, "value": "0"},
    )

    last_id_id = int(last_id.value)

    for character in EveCharacter.objects.filter(id__gt=last_id_id):
        try:
            logger.debug(f"Checking character: {character.character_name}")
            requests.get(f"{JABBERBOT_URL}/blacklist/{character.character_name}/")
            last_id_id = character.id
        except Exception as error:
            if "Connection aborted" in str(error):
                last_id_id = character.id
            else:
                logging.error(
                    f"Error connecting to Jabber! {error} : {type(error).__name__} : {get_full_class_name(error)}"
                )

    last_id.value = last_id_id

    last_id.save()


@shared_task
def new_account_discord_ping():
    settings_key = "NewAccountDiscordPingLastId"
    last_id, created = Settings.objects.get_or_create(
        setting_id=settings_key,
        defaults={"setting_id": settings_key, "value": "1"},
    )

    last_id_id = int(last_id.value)

    for aa_user in UserProfile.objects.filter(id__gt=last_id_id):
        try:
            logger.debug(
                f"Creating Discord thread for new user: {aa_user.user.username}"
            )

            thread_body = {
                "thread_name": aa_user.user.username,
                "content": f"AA Link: {settings.SITE_URL}/audit/r/{aa_user.main_character.character_id}/account/status",
            }

            send_discord_message(thread_body, HR_FORUM_WEBHOOK)

            last_id_id = aa_user.id
        except Exception as error:
            logging.error(f"Error connecting to discord! {error}")

    last_id.value = last_id_id

    last_id.save()


@shared_task
def structures_notification_unanchoring():
    settings_key = "StructuresNotificationUnanchoringLastId"
    last_id, created = Settings.objects.get_or_create(
        setting_id=settings_key,
        defaults={"setting_id": settings_key, "value": "1"},
    )

    last_id_id = int(last_id.value)

    for notification in StructuresNotification.objects.filter(
        id__gt=last_id_id, notif_type="StructureUnanchoring"
    ):

        parsed_text = notificaion.parsed_text()

        if not parsed_text:
            continue

        if "ownerCorpName" in parsed_text:
            owner_corp_name = parsed_text["ownerCorpName"]
        if "solarsystemID" in parsed_text:
            solar_system_id = parsed_text["solarsystemID"]
        if "structureTypeID" in parsed_text:
            structure_type_id = parsed_text["structureTypeID"]
        if "timeLeft" in parsed_text:
            time_left = parsed_text["timeLeft"]
        if "ownerCorpLinkData" in parsed_text:
            owner_corp_link_data = parsed_text["ownerCorpLinkData"][2]

        structure = StructuresStructure.objects.filter(
            structure_id=notification.structure_id
        ).first()


        timer = StructureTimersTimer.objects.create(
            timer_type="Unanchoring",
            location_details="",
            structure_name=structure.name if structure else "Unknown Structure",
            objective="FR",
            date=time_left,
            is_important=False,
            owner_name=owner_corp_name,
            is_opsec=False,
            visibility="UN",
            details_notes=f"Automatically created from Structures Notification for {notification.structure_name} at {datetime.datetime.now(timezone.utc).isoformat()}",
            eve_alliance_id=1,
            eve_corporation_id=370,
            eve_solar_system_id=solar_system_id,
            structure_type_id=structure_type_id,
            last_updated_at=datetime.datetime.now(timezone.utc).isoformat(),
        )

        last_id_id = notification.id

    last_id.value = last_id_id
    last_id.save()


            


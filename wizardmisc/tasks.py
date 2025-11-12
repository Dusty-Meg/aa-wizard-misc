"""App Tasks"""

# Standard Library
import json
import logging
import datetime

# Third Party
import requests
from celery import shared_task
import dhooks_lite

# Django
from django.conf import settings

# Alliance Auth
from allianceauth.authentication.models import UserProfile
from allianceauth.eveonline.models import (
    EveCharacter,
    EveCorporationInfo,
    EveAllianceInfo,
)

from eveuniverse.models.universe_1 import EveType
from eveuniverse.models.universe_2 import EveSolarSystem

from app_utils.datetime import ldap_timedelta_2_timedelta


from structures.models import Notification as StructuresNotification
from structures.models import Structure as StructuresStructure
from structuretimers.models import Timer as StructureTimersTimer
from structuretimers.models import DiscordWebhook as StructureTimersDiscordWebhook

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
            requests.get(f"{JABBERBOT_URL}/blacklist/{character.character_name}/", timeout=180)
            last_id_id = character.id
        except Exception as error:
            break
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

        parsed_text = notification.parsed_text()

        if not parsed_text:
            continue

        if "ownerCorpName" in parsed_text:
            owner_corp_name = parsed_text["ownerCorpName"]
        if "solarsystemID" in parsed_text:
            solar_system_id = parsed_text["solarsystemID"]
        if "structureTypeID" in parsed_text:
            structure_type_id = parsed_text["structureTypeID"]
        if "structureID" in parsed_text:
            structure_id = parsed_text["structureID"]
        if "timeLeft" in parsed_text:
            time_left = parsed_text["timeLeft"]
        if "ownerCorpLinkData" in parsed_text:
            owner_corp_link_data = parsed_text["ownerCorpLinkData"][2]

        structure = StructuresStructure.objects.filter(id=structure_id).first()

        structure_name = structure.name if structure else "Unknown Structure"

        corp = EveCorporationInfo.objects.filter(
            corporation_id=owner_corp_link_data
        ).first()

        alliance = None
        if corp.alliance_id is not None:
            alliance = EveAllianceInfo.objects.filter(id=corp.alliance_id).first()

        eve_time = notification.timestamp + ldap_timedelta_2_timedelta(time_left)

        timer = StructureTimersTimer.objects.filter(
            eve_solar_system_id=solar_system_id,
            structure_name=structure_name,
            timer_type="UA",
        ).first()

        solar_system = EveSolarSystem.objects.filter(id=solar_system_id).first()

        structure_type = EveType.objects.filter(id=structure_type_id).first()

        if timer:
            timer.date = eve_time
            timer.owner_name = owner_corp_name
            timer.details_notes = f"Updated from Structures Notification for {owner_corp_name} at {datetime.datetime.now(datetime.timezone.utc).isoformat()}"
            timer.eve_alliance = alliance
            timer.eve_corporation = corp
            timer.last_updated_at = str(
                datetime.datetime.now(datetime.timezone.utc).isoformat()
            )
            timer.save()
        else:
            timer = StructureTimersTimer.objects.create(
                timer_type="UA",
                location_details="",
                structure_name=structure.name if structure else "Unknown Structure",
                objective="FR",
                date=eve_time,
                is_important=False,
                owner_name=owner_corp_name,
                is_opsec=False,
                visibility="UN",
                details_notes=f"Automatically created from Structures Notification for {owner_corp_name} at {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
                eve_alliance=alliance,
                eve_corporation=corp,
                eve_solar_system=solar_system,
                structure_type=structure_type,
                last_updated_at=str(
                    datetime.datetime.now(datetime.timezone.utc).isoformat()
                ),
            )
            timer.save()

        last_id_id = notification.id

    last_id.value = last_id_id
    last_id.save()


@shared_task
def alert_upcoming_unanchoring():
    timers = (
        StructureTimersTimer.objects.filter(
            timer_type="UA", date__gt=datetime.datetime.now(datetime.timezone.utc)
        ).exclude(owner_name="Echelon Research")
        .order_by("date")
        .all()[:100]
    )

    if not timers:
        return

    webhook = StructureTimersDiscordWebhook.objects.filter(is_enabled=True).first()

    embeds = []

    if len(timers) <= 10:
        unanchoring_table = []
        structures_names = ""
        unanchoring_dates = ""
        time_until_unanchoring = ""
        for timer in timers:
            structures_names += (
                f"{timer.structure_name} ({timer.eve_solar_system.name})\n"
            )
            unanchoring_dates += f"<t:{timer.date.strftime('%s')}:f>\n"
            time_until_unanchoring += f"<t:{timer.date.strftime('%s')}:R>\n"
        unanchoring_table.append(
            dhooks_lite.Field("Structure", structures_names, inline=True)
        )
        unanchoring_table.append(
            dhooks_lite.Field("Unanchoring Date", unanchoring_dates, inline=True)
        )
        unanchoring_table.append(
            dhooks_lite.Field(
                "Time Until Unanchoring", time_until_unanchoring, inline=True
            )
        )

        e1 = dhooks_lite.Embed(
            fields=unanchoring_table,
        )

        embeds.append(e1)
    else:
        for i in range(0, len(timers), 10):
            unanchoring_table = []
            structures_names = ""
            unanchoring_dates = ""
            time_until_unanchoring = ""
            for timer in timers[i : i + 10]:
                structures_names += (
                    f"{timer.structure_name} ({timer.eve_solar_system.name})\n"
                )
                unanchoring_dates += f"<t:{timer.date.strftime('%s')}:f>\n"
                time_until_unanchoring += f"<t:{timer.date.strftime('%s')}:R>\n"
            unanchoring_table.append(
                dhooks_lite.Field("Structure", structures_names, inline=True)
            )
            unanchoring_table.append(
                dhooks_lite.Field("Unanchoring Date", unanchoring_dates, inline=True)
            )
            unanchoring_table.append(
                dhooks_lite.Field(
                    "Time Until Unanchoring", time_until_unanchoring, inline=True
                )
            )

            e1 = dhooks_lite.Embed(
                fields=unanchoring_table,
            )
            embeds.append(e1)

    hook = dhooks_lite.Webhook(webhook.url)

    hook.execute(
        "Upcoming Unanchoring Timers",
        username="Structure Timers",
        embeds=embeds,
    )

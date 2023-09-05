"""
New Account Discord Ping test
"""

# Standard Library
from unittest import mock

# Django
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership, UserProfile
from allianceauth.eveonline.models import EveCharacter
from allianceauth.tests.auth_utils import AuthUtils

from .. import models as local_models
from .. import tasks as local_tasks


def mocked_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    if (
        kwargs["url"]
        == "https://discord.com/api/webhooks/44/HCdVva_OSpjEffffgYUnV6QgggLsAt-tTBSLPl3U4335rM3Rd9"
    ):
        return MockResponse({}, 200)

    return MockResponse(None, 404)


class TestExample(TestCase):
    """
    TestExample
    """

    @classmethod
    def setUpClass(cls):
        cls.factory = RequestFactory()
        UserProfile.objects.all().delete()
        EveCharacter.objects.all().delete()
        User.objects.all().delete()
        local_models.Settings.objects.all().delete()

        userids = range(1, 4)

        local_models.Settings.objects.create(
            setting_id="NewAccountDiscordPingLastId", value="1"
        )

        users = []
        characters = []
        for uid in userids:
            user = AuthUtils.create_user(f"User_{uid}")
            main_char = AuthUtils.add_main_character_2(
                user,
                f"Main {uid}",
                uid,
                corp_id=1,
                corp_name="Test Corp 1",
                corp_ticker="TST1",
            )
            CharacterOwnership.objects.create(
                user=user, character=main_char, owner_hash=f"main{uid}"
            )

            characters.append(main_char)
            users.append(user)

        super().setUpClass()

    @mock.patch("requests.post", side_effect=mocked_requests_post)
    def test_can_call_discord(self, mock_post):
        local_tasks.new_account_discord_ping()

        self.assertIn(
            mock.call(
                url="https://discord.com/api/webhooks/44/HCdVva_OSpjEffffgYUnV6QgggLsAt-tTBSLPl3U4335rM3Rd9",
                data='{"thread_name": "User_2", "content": "AA Link: https://example.com/audit/r/2/account/status"}',
                headers={"Content-Type": "application/json"},
            ),
            mock_post.call_args_list,
        )

        self.assertEqual(
            "3",
            local_models.Settings.objects.get(
                setting_id="NewAccountDiscordPingLastId"
            ).value,
        )

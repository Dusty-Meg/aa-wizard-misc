"""
New Account Discord Ping test
"""

# Standard Library
from unittest import mock

# Django
from django.test import RequestFactory, TestCase

# Alliance Auth
from allianceauth.authentication.models import UserProfile

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
        args[0]
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
        local_models.Settings.objects.all().delete()

        local_models.Settings.objects.create(
            setting_id="NewAccountDiscordPingLastId", value="1"
        )

        UserProfile.objects.create(
            main_character_id=None, state_id=1, user_id=1, language="", night_mode=None
        )

        UserProfile.objects.create(
            main_character_id=22, state_id=1, user_id=2, language="", night_mode=None
        )

        UserProfile.objects.create(
            main_character_id=33, state_id=1, user_id=3, language="", night_mode=None
        )

        super().setUpClass()

    @mock.patch("requests.post", side_effect=mocked_requests_post)
    def test_can_call_discord(self, mock_post):
        local_tasks.new_account_discord_ping()

        self.assertIn(
            mock.call(
                "https://discord.com/api/webhooks/44/HCdVva_OSpjEffffgYUnV6QgggLsAt-tTBSLPl3U4335rM3Rd9"
            ),
            mock_post.call_args_list,
        )

        self.assertEqual(
            "3",
            local_models.Settings.objects.get(
                setting_id="NewAccountDiscordPingLastId"
            ).value,
        )

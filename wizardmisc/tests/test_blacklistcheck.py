"""
Blacklist check test
"""

# Standard Library
from unittest import mock

# Django
from django.test import RequestFactory, TestCase

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter

from .. import models as local_models
from .. import tasks as local_tasks


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    if args[0] == "http://192.168.234.233:5000/blacklist/Alt 1/":
        return MockResponse({}, 200)
    elif args[0] == "http://192.168.234.233:5000/blacklist/Alt 2/":
        return MockResponse({}, 200)

    return MockResponse(None, 404)


class TestExample(TestCase):
    """
    TestExample
    """

    @classmethod
    def setUpClass(cls):
        cls.factory = RequestFactory()
        EveCharacter.objects.all().delete()
        local_models.Settings.objects.all().delete()

        local_models.Settings.objects.create(setting_id="BlacklistLastId", value="1")

        EveCharacter.objects.create(
            character_name="Alt 1",
            character_id=1,
            corporation_name="Test Corp 1",
            corporation_id=2,
            corporation_ticker="TST2",
        )

        EveCharacter.objects.create(
            character_name="Alt 2",
            character_id=2,
            corporation_name="Test Corp 1",
            corporation_id=2,
            corporation_ticker="TST2",
        )

        EveCharacter.objects.create(
            character_name="Alt 3",
            character_id=3,
            corporation_name="Test Corp 1",
            corporation_id=2,
            corporation_ticker="TST2",
        )

        super().setUpClass()

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_can_call_blacklist(self, mock_get):
        local_tasks.blacklist_check()

        self.assertNotIn(
            mock.call("http://192.168.234.233:5000/blacklist/Alt 1"),
            mock_get.call_args_list,
        )
        self.assertIn(
            mock.call("http://192.168.234.233:5000/blacklist/Alt 2"),
            mock_get.call_args_list,
        )
        self.assertIn(
            mock.call("http://192.168.234.233:5000/blacklist/Alt 3"),
            mock_get.call_args_list,
        )

        self.assertEqual(
            "3", local_models.Settings.objects.get(setting_id="BlacklistLastId").value
        )

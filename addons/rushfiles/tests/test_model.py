# -*- coding: utf-8 -*-

from base64 import decode
import jwt
import mock
import pytest
import unittest

from nose.tools import (
    assert_equal,assert_true
)

from addons.rushfiles.models import NodeSettings, RushFilesProvider
from addons.rushfiles.client import RushFilesAuthClient


class TestProvider(unittest.TestCase):
    def setUp(self):
        super(TestProvider, self).setUp()
        self.provider = RushFilesProvider()

    @mock.patch.object(RushFilesAuthClient, 'userinfo')
    def test_handle_callback(self, mock_client):
        fake_response = {'access_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJwcmltYXJ5X2RvbWFpbiI6ImZha2VAZmFrZS5uZXQifQ._CTx5dIZ0piHbqnF63NV-G6nuFs9uN-9q-pnR0X5HYE'}

        fake_info = {
            'User': {
                'UserId': 'fake@fake.net',
                'Email': 'kkitazawa@tsukaeru.net',
                'Name': 'fake fake'
            }
        }

        mock_client.return_value = fake_info

        res = self.provider.handle_callback(fake_response)

        assert_equal(res['provider_id'], 'fake@fake.net')
        assert_equal(res['display_name'], 'fake fake')
        assert_equal(res['profile_url'], None)

class TestNodeSettings(unittest.TestCase):
    def test_handle_callback(self):
        assert_true(True)
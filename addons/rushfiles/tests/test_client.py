import unittest

import pytest
import mock
from nose.tools import assert_true, assert_equal  # noqa (PEP8 asserts)
from addons.rushfiles.client import RushFilesClient
import jwt
from requests import Response

class FakeResponse():
        def __init__(self):
            self.response =  {
            "Data": [
                {
                    "Id": "fake",
                    "Name": "fakeName",
                }
            ],
            "Message": "string",
            "ResponseInfo": {
                "ResponseCode": 1000,
                "Reference": "string"
            }
        }

        def json(self):
            return self.response

class TestClient(unittest.TestCase):

    def setUp(self):
        super(TestClient, self).setUp()
        self.client = RushFilesClient()

    @mock.patch.object(jwt, 'decode')
    @mock.patch.object(RushFilesClient, '_make_request')
    def test_shares_only_primary_domain(self, mock_response, mock_payload):
        fake_response = FakeResponse()

        mock_payload.return_value = {
            "primary_domain": "fake.net",
        }
        mock_response.return_value = fake_response
        res = self.client.shares("fakeId")

        assert_equal(len(res), 1)
        assert_equal(res[0]["Id"], fake_response.response["Data"][0]["Id"])
        assert_equal(res[0]["Name"], fake_response.response["Data"][0]["Name"])

    @mock.patch.object(jwt, 'decode')
    @mock.patch.object(RushFilesClient, '_make_request')
    def test_shares_one_domain(self,mock_response, mock_payload):
        fake_response = FakeResponse()

        mock_payload.return_value = {
            "primary_domain": "fake.net",
            "domains": "fake.com"
        }
        mock_response.return_value = fake_response
        res = self.client.shares("fakeId")

        assert_equal(len(res), 2)
        assert_equal(res[0]["Id"], fake_response.response["Data"][0]["Id"])
        assert_equal(res[0]["Name"], fake_response.response["Data"][0]["Name"])

    @mock.patch.object(jwt, 'decode')
    @mock.patch.object(RushFilesClient, '_make_request')
    def test_shares_some_domains(self,mock_response, mock_payload):
        fake_response = FakeResponse()

        mock_payload.return_value = {
            "primary_domain": "fake.net",
            "domains": [
                "fake.com",
                "fake.jp"
            ]
        }
        mock_response.return_value = fake_response
        res = self.client.shares("fakeId")

        assert_equal(len(res), 3)
        assert_equal(res[0]["Id"], fake_response.response["Data"][0]["Id"])
        assert_equal(res[0]["Name"], fake_response.response["Data"][0]["Name"])

# from nose.tools import *  # noqa
import unittest

import mock
import pytest
from nose.tools import (assert_false, assert_true,
                        assert_equal, assert_is_none)

from addons.base.tests.models import (
    OAuthAddonNodeSettingsTestSuiteMixin,
    OAuthAddonUserSettingTestSuiteMixin
)
from addons.integromat import SHORT_NAME, FULL_NAME
from addons.integromat import settings
from addons.integromat.models import NodeSettings
from addons.integromat.tests.factories import (
    IntegromatUserSettingsFactory,
    IntegromatNodeSettingsFactory,
    IntegromatAccountFactory
)
from framework.auth import Auth
from osf_tests.factories import ProjectFactory, DraftRegistrationFactory
from tests.base import get_default_metaschema

pytestmark = pytest.mark.django_db


class TestUserSettings(OAuthAddonUserSettingTestSuiteMixin, unittest.TestCase):

    short_name = SHORT_NAME
    full_name = FULL_NAME
    ExternalAccountFactory = IntegromatAccountFactory


class TestNodeSettings(OAuthAddonNodeSettingsTestSuiteMixin, unittest.TestCase):

    short_name = SHORT_NAME
    full_name = FULL_NAME
    ExternalAccountFactory = IntegromatAccountFactory
    NodeSettingsFactory = IntegromatNodeSettingsFactory
    NodeSettingsClass = NodeSettings
    UserSettingsFactory = IntegromatUserSettingsFactory

    def test_registration_settings(self):
        registration = ProjectFactory()
        clone, message = self.node_settings.after_register(
            self.node, registration, self.user,
        )
        assert_is_none(clone)

    def test_before_register_no_settings(self):
        self.node_settings.user_settings = None
        message = self.node_settings.before_register(self.node, self.user)
        assert_false(message)

    def test_before_register_no_auth(self):
        self.node_settings.external_account = None
        message = self.node_settings.before_register(self.node, self.user)
        assert_false(message)

    def test_before_register_settings_and_auth(self):
        message = self.node_settings.before_register(self.node, self.user)
        assert_true(message)

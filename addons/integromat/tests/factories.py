# -*- coding: utf-8 -*-
"""Factories for the Integromat addon."""
import factory
from factory.django import DjangoModelFactory

from addons.integromat import SHORT_NAME
from addons.integromat.models import (
    UserSettings,
    NodeSettings
)
from osf_tests.factories import UserFactory, ProjectFactory, ExternalAccountFactory


class integromatAccountFactory(ExternalAccountFactory):
    provider = SHORT_NAME
    provider_id = factory.Sequence(lambda n: 'id-{0}'.format(n))
    oauth_key = factory.Sequence(lambda n: 'key-{0}'.format(n))
    webhook_url = factory.Sequence(lambda n: 'webhook-{0}'.format(n))
    display_name = 'Integromat Fake User'


class integromatUserSettingsFactory(DjangoModelFactory):
    class Meta:
        model = UserSettings

    owner = factory.SubFactory(UserFactory)


class integromatNodeSettingsFactory(DjangoModelFactory):
    class Meta:
        model = NodeSettings

    owner = factory.SubFactory(ProjectFactory)
    user_settings = factory.SubFactory(integromatUserSettingsFactory)

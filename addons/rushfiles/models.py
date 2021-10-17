# -*- coding: utf-8 -*-
"""Persistence layer for the google drive addon.
"""
from addons.base.models import (BaseOAuthNodeSettings, BaseOAuthUserSettings,
                                BaseStorageAddon)
from django.db import models

from osf.models.external import ExternalProvider
from osf.models.files import File, Folder, BaseFileNode
from addons.rushfiles import settings
from addons.rushfiles.serializer import RushFilesSerializer

import jwt

class RushFilesFileNode(BaseFileNode):
    _provider = 'rushfiles'


class RushFilesFolder(RushFilesFileNode, Folder):
    pass


class RushFilesFile(RushFilesFileNode, File):
    pass


class RushFilesProvider(ExternalProvider):
    name = 'RushFiles'
    short_name = 'rushfiles'

    client_id = settings.CLIENT_ID
    client_secret = settings.CLIENT_SECRET

    auth_url_base = '{}{}'.format(settings.OAUTH_BASE_URL, 'authorize')
    callback_url = '{}{}'.format(settings.OAUTH_BASE_URL, 'token')

    default_scopes = settings.OAUTH_SCOPE

    def handle_callback(self, response):
        # Should we better verify?
        payload = jwt.decode(response['access_token'], verify=False)
        #TODO: get user name from RushFiles
        return {
            'provider_id': payload['sub'],
            'display_name': 'Wiktor Klonowski',
            'profile_url': None
        }

    def fetch_access_token(self, force_refresh=False):
        self.refresh_oauth_key(force=force_refresh)
        return self.account.oauth_key


class UserSettings(BaseOAuthUserSettings):
    oauth_provider = RushFilesProvider
    serializer = RushFilesSerializer


class NodeSettings(BaseOAuthNodeSettings, BaseStorageAddon):
    oauth_provider = RushFilesProvider
    serializer = RushFilesSerializer

    share_id = models.TextField(null=True, blank=True)
    share_name = models.TextField(null=True, blank=True)
    domain = models.TextField(null=True, blank=True)
    user_settings = models.ForeignKey(UserSettings, null=True, blank=True, on_delete=models.CASCADE)

    @property
    def folder_id(self):
        return self.share_id or None

    @property
    def folder_name(self):
        return self.share_name or None

    @property
    def folder_path(self):
        return self.share_id or None
    

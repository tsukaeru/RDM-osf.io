# -*- coding: utf-8 -*-
import logging
import os
from django.db import models

from framework.auth import Auth
from framework.exceptions import HTTPError
from osf.models.external import ExternalProvider
from osf.models.files import File, Folder, BaseFileNode
from addons.base import exceptions
from addons.base.models import (BaseOAuthNodeSettings, BaseOAuthUserSettings, BaseStorageAddon)
from addons.googledriveinstitutions import settings as drive_settings
from addons.googledriveinstitutions import utils
from addons.googledriveinstitutions.client import (GoogleAuthClient, GoogleDriveInstitutionsClient)
from addons.googledriveinstitutions.serializer import GoogleDriveInstitutionsSerializer
from website.util import api_v2_url, timestamp

logger = logging.getLogger(__name__)

ENABLE_DEBUG = True

def DEBUG(msg):
    if ENABLE_DEBUG:
        logger.error(u'DEBUG_googledriveinstitutions: {}'.format(msg))

# TODO make googledriveinstitutions "pathfollowing"
# A migration will need to be run that concats
# folder_path and filenode.path
# class GoogleDriveInstitutionsFileNode(PathFollowingFileNode):
class GoogleDriveInstitutionsFileNode(BaseFileNode):
    _provider = 'googledriveinstitutions'
    FOLDER_ATTR_NAME = 'folder_path'


class GoogleDriveInstitutionsFolder(GoogleDriveInstitutionsFileNode, Folder):
    pass


class GoogleDriveInstitutionsFile(GoogleDriveInstitutionsFileNode, File):
    HASH_TYPE = 'sha512'

    @property
    def _hashes(self):
        try:
            DEBUG('sha512(_hashes): {}'.format(self._history[-1]['extra']['hashes'][self.HASH_TYPE]))
            return {self.HASH_TYPE: self._history[-1]['extra']['hashes'][self.HASH_TYPE]}
        except (IndexError, KeyError) as e:
            logger.exception('Raise Exception: {}'.format(e))
            return None

    # return (hash_type, hash_value)
    def get_hash_for_timestamp(self):
        DEBUG('self._hashes: {}'.format(self._hashes))
        if self._hashes:
            sha512 = self._hashes.get(self.HASH_TYPE)
            DEBUG('sha512: {}'.format(sha512))
            if sha512:
                return timestamp.HASH_TYPE_SHA512, sha512
        return None, None  # unsupported

    def _my_node_settings(self):
        node = self.target
        if node:
            addon = node.get_addon(self.provider)
            if addon:
                DEBUG('_my_node_settings addon: {}'.format(addon))
                return addon
        return None

    def get_timestamp(self):
        node_settings = self._my_node_settings()
        if node_settings:
            return utils.get_timestamp(node_settings, self.path)
        return None, None, None

    def set_timestamp(self, timestamp_data, timestamp_status, context):
        node_settings = self._my_node_settings()
        if node_settings:
            utils.set_timestamp(node_settings, self.path, timestamp_data,
                                timestamp_status, context=context)

class GoogleDriveInstitutionsProvider(ExternalProvider):
    name = 'Google Drive in G Suite / Google Workspace'
    short_name = 'googledriveinstitutions'

    client_id = drive_settings.CLIENT_ID
    client_secret = drive_settings.CLIENT_SECRET

    auth_url_base = '{}{}'.format(drive_settings.OAUTH_BASE_URL, 'auth?access_type=offline&approval_prompt=force')
    callback_url = '{}{}'.format(drive_settings.API_BASE_URL, 'oauth2/v3/token')
    auto_refresh_url = callback_url
    refresh_time = drive_settings.REFRESH_TIME
    expiry_time = drive_settings.EXPIRY_TIME

    default_scopes = drive_settings.OAUTH_SCOPE
    _auth_client = GoogleAuthClient()
    _drive_client = GoogleDriveInstitutionsClient()

    def handle_callback(self, response):
        client = self._auth_client
        info = client.userinfo(response['access_token'])
        return {
            'provider_id': info['sub'],
            'display_name': info['name'],
            'profile_url': info.get('profile', None)
        }

    def fetch_access_token(self, force_refresh=False):
        self.refresh_oauth_key(force=force_refresh)
        return self.account.oauth_key


class UserSettings(BaseOAuthUserSettings):
    oauth_provider = GoogleDriveInstitutionsProvider
    serializer = GoogleDriveInstitutionsSerializer


class NodeSettings(BaseOAuthNodeSettings, BaseStorageAddon):
    oauth_provider = GoogleDriveInstitutionsProvider
    provider_name = 'googledriveinstitutions'

    folder_id = models.TextField(null=True, blank=True)
    folder_path = models.TextField(null=True, blank=True)
    serializer = GoogleDriveInstitutionsSerializer
    user_settings = models.ForeignKey(UserSettings, null=True, blank=True, on_delete=models.CASCADE)

    _api = None

    @property
    def api(self):
        """Authenticated ExternalProvider instance"""
        if self._api is None:
            self._api = GoogleDriveInstitutionsProvider(self.external_account)
        return self._api

    @property
    def complete(self):
        return bool(self.has_auth and self.user_settings.verify_oauth_access(
            node=self.owner,
            external_account=self.external_account,
            metadata={'folder': self.folder_id}
        ))

    @property
    def folder_name(self):
        if not self.folder_id:
            return None

        if self.folder_path != '/':
            return os.path.split(self.folder_path)[1]
        else:
            return '/ (Full Google Drive in G Suite / Google Workspace)'

    def clear_settings(self):
        self.folder_id = None
        self.folder_path = None

    def get_folders(self, **kwargs):
        node = self.owner

        # Defaults exist when called by the API, but are `None`
        path = kwargs.get('path') or ''
        folder_id = kwargs.get('folder_id') or 'root'

        try:
            access_token = self.fetch_access_token()
        except exceptions.InvalidAuthError:
            raise HTTPError(403)

        client = GoogleDriveInstitutionsClient(access_token)
        if folder_id == 'root':
            rootFolderId = client.rootFolderId()
            DEBUG('rootFolderId: {}'.format(rootFolderId))

            return [{
                'addon': self.config.short_name,
                'path': '/',
                'kind': 'folder',
                'id': rootFolderId,
                'name': '/ (Full Google Drive in G Suite / Google Workspace)',
                'urls': {
                    'folders': api_v2_url('nodes/{}/addons/googledriveinstitutions/folders/'.format(self.owner._id),
                        params={
                            'path': '/',
                            'id': rootFolderId
                    })
                }
            }]

        contents = [
            utils.to_hgrid(item, node, path=path)
            for item in client.folders(folder_id)
        ]
        return contents

    def set_folder(self, folder, auth):
        """Configure this addon to point to a Google Drive folder

        :param dict folder:
        :param User user:
        """
        self.folder_id = folder['id']
        self.folder_path = folder['path']
        DEBUG('folder_id: {}'.format(self.folder_id))

        # Tell the user's addon settings that this node is connecting
        self.user_settings.grant_oauth_access(
            node=self.owner,
            external_account=self.external_account,
            metadata={'folder': self.folder_id}
        )
        # Performs a save on self.user_settings
        self.save()

        self.nodelogger.log('folder_selected', save=True)

    @property
    def selected_folder_name(self):
        if self.folder_id is None:
            return ''
        elif self.folder_id == 'root':
            return 'Full Google Drive in G Suite / Google Workspace'
        else:
            return self.folder_name

    def deauthorize(self, auth=None, add_log=True, save=False):
        """Remove user authorization from this node and log the event."""

        if add_log:
            extra = {'folder_id': self.folder_id}
            self.nodelogger.log(action='node_deauthorized', extra=extra, save=True)

        self.clear_settings()
        self.clear_auth()

        if save:
            self.save()

    def serialize_waterbutler_credentials(self):
        if not self.has_auth:
            raise exceptions.AddonError('Addon is not authorized')
        return {'token': self.fetch_access_token()}

    def serialize_waterbutler_settings(self):
        if not self.folder_id:
            raise exceptions.AddonError('Folder is not configured')

        return {
            'folder': {
                'id': self.folder_id,
                'name': self.folder_name,
                'path': self.folder_path
            }
        }

    def create_waterbutler_log(self, auth, action, metadata):
        url = self.owner.web_url_for('addon_view_or_download_file', path=metadata['path'], provider='googledriveinstitutions')

        self.owner.add_log(
            'googledriveinstitutions_{0}'.format(action),
            auth=auth,
            params={
                'project': self.owner.parent_id,
                'node': self.owner._id,
                'path': metadata['path'],
                'folder': self.folder_path,

                'urls': {
                    'view': url,
                    'download': url + '?action=download'
                },
            },
        )

    def fetch_access_token(self):
        return self.api.fetch_access_token()

    def after_delete(self, user):
        self.deauthorize(Auth(user=user), add_log=True, save=True)

    def on_delete(self):
        self.deauthorize(add_log=False)
        self.save()

class Channel():
    user = models.TextField(null=True, blank=True)
    channelId = models.TextField(null=True, blank=True)
    pageToken = models.TextField(null=True, blank=True)

# -*- coding: utf-8 -*-
import logging
import os
from django.db import models

from framework.auth import Auth
from framework.exceptions import HTTPError
from osf.models.external import ExternalProvider, ExternalAccount
from osf.models.files import File, Folder, BaseFileNode
from osf.utils.permissions import ADMIN, READ, WRITE
from addons.base import exceptions
from addons.base import institutions_utils as inst_utils
from addons.base.institutions_utils import (
    InstitutionsNodeSettings,
    InstitutionsStorageAddon
)
# from addons.base.models import (BaseOAuthNodeSettings, BaseOAuthUserSettings, BaseStorageAddon)
from addons.base.models import BaseOAuthUserSettings
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

    @property
    def _hashes(self):
        try:
            return {'md5': self._history[-1]['extra']['hashes']['md5']}
        except (IndexError, KeyError) as e:
            logger.exception('Raise Exception: {}'.format(e))
            return None


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

    def __init__(self, account=None):

        if account:
            self.account = account
        else:
            self.account = ExternalAccount(
                provider=self.short_name,
                provider_name=self.name
            )

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


class NodeSettings(InstitutionsNodeSettings, InstitutionsStorageAddon):
    FULL_NAME = 'Google Drive in G Suite / Google Workspace'
    SHORT_NAME = 'googledriveinstitutions'

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

    def fetch_access_token(self):
        return self.api.fetch_access_token()

    def on_delete(self):
        self.deauthorize(add_log=False)
        self.save()

    @classmethod
    def addon_settings(cls):
        return drive_settings

    @classmethod
    def get_provider(cls, external_account):
        return GoogleDriveInstitutionsProvider(external_account)

    @classmethod
    def get_debug_provider(cls):
        if not (drive_settings.DEBUG_URL
                and drive_settings.DEBUG_USER
                and drive_settings.DEBUG_PASSWORD):
            return None

        class DebugProvider(object):
            host = drive_settings.DEBUG_URL
            username = drive_settings.DEBUG_USER
            password = drive_settings.DEBUG_PASSWORD
        return DebugProvider()

    @classmethod
    def get_client(cls, provider):
        client = GoogleDriveInstitutionsClient(provider.account)
        return client

    @classmethod
    def _list_count(cls, client, base_folder):
        count = 0
        for item in client.folders(base_folder):  # may raise
            count += 1
        return count

    @classmethod
    def can_access(cls, client, base_folder):
        cls._list_count(client, base_folder)

    @classmethod
    def create_folder(cls, client, base_folder, name):
        logger.info(u'create folder: {} ({})'.format(name, base_folder))
        client.mkdir(base_folder, name)

    @classmethod
    def remove_folder(cls, client, base_folder, name):
        logger.info(u'delete folder: {} ({})'.format(name, base_folder))
        client.rmdir(base_folder, name)

    @classmethod
    def rename_folder(cls, client, base_folder, old_name, new_name):
        logger.info(u'rename folder')
        client.rename(base_folder, old_name, new_name)

    @classmethod
    def root_folder_format(cls):
        return drive_settings.ROOT_FOLDER_FORMAT

    @property
    def exists(self):
        try:
            self._list_count(self.client, self.base_folder)
            return True
        except Exception:
            return False

    # override
    def sync_title(self):
        super(NodeSettings, self).sync_title()
        # share again to rename folder name for shared users
        self._delete_all_shares()
        self.sync_contributors()

    def _delete_all_shares(self):
        c = self.client
        for item in c.get_shares(path=self.root_folder_fullpath):
            if item.get_share_type() != c.OCS_SHARE_TYPE_USER:
                continue
            user_id = item.get_share_with()
            share_id = item.get_id()
            try:
                c.delete_share(share_id)
            except Exception as e:
                logger.warning(u'delete_share failed: user_id={}: {}'.format(user_id, str(e)))

    def sync_contributors(self):
        node = self.owner
        c = self.client

        # 1 (read only)
        NC_READ = c.OCS_PERMISSION_READ
        # 7 (read, write, cannot DELETE)
        NC_WRITE = NC_READ | c.OCS_PERMISSION_UPDATE | c.OCS_PERMISSION_CREATE
        # 31 (NC_WRITE | OCS_PERMISSION_DELETE | OCS_PERMISSION_SHARE)
        NC_ADMIN = c.OCS_PERMISSION_ALL

        def _grdm_perms_to_nc_perms(node, user):
            if node.has_permission(user, ADMIN):
                return NC_ADMIN
            elif node.has_permission(user, WRITE):
                return NC_WRITE
            elif node.has_permission(user, READ):
                return NC_READ
            else:
                return None

        # nc_user_id -> (contributor(OSFUser), nc_permissions)
        grdm_member_all_dict = {}
        for cont in node.contributors.iterator():
            if cont.is_active and cont.eppn:
                nc_user_id = self.osfuser_to_extuser(cont)
                if not nc_user_id:
                    continue
                grdm_perms = node.get_permissions(cont)
                nc_perms = _grdm_perms_to_nc_perms(node, cont)
                if nc_perms is None:
                    continue
                grdm_member_all_dict[nc_user_id] = (cont, nc_perms)

        grdm_member_users = [
            user_id for user_id in grdm_member_all_dict.keys()
        ]

        # nc_user_id -> (nc_share_id, nc_permissions)
        nc_member_all_dict = {}
        for item in c.get_shares(path=self.root_folder_fullpath):  # may raise
            if item.get_share_type() == c.OCS_SHARE_TYPE_USER:
                nc_member_all_dict[item.get_share_with()] \
                    = (item.get_id(), item.get_permissions())

        nc_member_users = [
            user_id for user_id in nc_member_all_dict.keys()
        ]

        # share_file_with_user() cannot share a file with myself.
        my_user_id = self.provider.username
        grdm_member_users_set = set(grdm_member_users) - set([my_user_id])
        nc_member_users_set = set(nc_member_users) - set([my_user_id])

        add_users_set = grdm_member_users_set - nc_member_users_set
        remove_users_set = nc_member_users_set - grdm_member_users_set
        update_users_set = grdm_member_users_set & nc_member_users_set

        DEBUG(u'add_users_set: ' + str(add_users_set))
        DEBUG(u'remove_users_set: ' + str(remove_users_set))
        DEBUG(u'update_users_set: ' + str(update_users_set))

        first_exception = None
        for user_id in add_users_set:
            grdm_info = grdm_member_all_dict.get(user_id)
            if grdm_info is None:
                continue  # unexpected
            osfuser, perms = grdm_info
            try:
                c.share_file_with_user(self.root_folder_fullpath, user_id, perms=perms)
            except Exception as e:
                if first_exception:
                    first_exception = e
                logger.warning(u'share_file_with_user failed: user_id={}: {}'.format(user_id, str(e)))

        for user_id in remove_users_set:
            nc_info = nc_member_all_dict.get(user_id)
            if nc_info is None:
                continue  # unexpected
            share_id, perms = nc_info
            try:
                c.delete_share(share_id)
            except Exception as e:
                if first_exception:
                    first_exception = e
                logger.warning(u'delete_share failed: user_id={}: {}'.format(user_id, str(e)))

        for user_id in update_users_set:
            nc_info = nc_member_all_dict.get(user_id)
            if nc_info is None:
                continue  # unexpected
            share_id, nc_perms = nc_info
            grdm_info = grdm_member_all_dict.get(user_id)
            if grdm_info is None:
                continue  # unexpected
            osfuser, grdm_perms = grdm_info
            if nc_perms != grdm_perms:
                try:
                    c.update_share(share_id, perms=grdm_perms)
                except Exception as e:
                    if first_exception:
                        first_exception = e
                    logger.warning(u'update_share failed: user_id={}: {}'.format(user_id, str(e)))

        if first_exception:
            raise first_exception

    def serialize_waterbutler_credentials_impl(self):
        return {'token': self.fetch_access_token()}

    def serialize_waterbutler_settings_impl(self):
        return {
            'folder': {
                'id': self.folder_id,
                'name': self.folder_name,
                'path': self.folder_path
            }
        }

    def copy_folders(self, dest_addon):
        root_folder = '/' + self.root_folder_fullpath.strip('/') + '/'
        root_folder_len = len(root_folder)
        c = self.client
        destc = dest_addon.client
        for item in c.list(root_folder, depth='infinity'):  # may raise
            # print(item.path)
            if item.is_dir() and item.path.startswith(root_folder):
                subpath = item.path[root_folder_len:]
                newpath = dest_addon.root_folder_fullpath + '/' + subpath
                logger.debug(u'copy_folders: mkdir({})'.format(newpath))
                destc.mkdir(newpath)


inst_utils.register(NodeSettings)
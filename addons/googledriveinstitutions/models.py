# -*- coding: utf-8 -*-
import logging
import os
from django.db import models
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from flask import request
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import (AccessDeniedError, InvalidGrantError,
    TokenExpiredError, MissingTokenError)
from requests.exceptions import HTTPError as RequestsHTTPError

from framework.auth import Auth
from framework.exceptions import HTTPError
from framework.exceptions import HTTPError, PermissionsError
from framework.sessions import session
from osf.models.external import ExternalProvider, ExternalAccount
from osf.models.files import File, Folder, BaseFileNode
from osf.models.node import Node
from osf.models.contributor import Contributor
from osf.models.institution import Institution
from osf.models.rdm_addons import RdmAddonOption
from addons.base import exceptions
from addons.base.models import (BaseOAuthNodeSettings, BaseOAuthUserSettings, BaseStorageAddon)
from addons.base.models import BaseNodeSettings
from addons.base.institutions_utils import KEYNAME_BASE_FOLDER
from addons.googledriveinstitutions import settings
from addons.googledriveinstitutions import utils
from addons.googledriveinstitutions.apps import GoogleDriveInstitutionsAddonConfig
from addons.googledriveinstitutions.client import (GoogleAuthClient, GoogleDriveInstitutionsClient)
from addons.googledriveinstitutions.serializer import GoogleDriveInstitutionsSerializer
from admin.rdm.utils import get_institution_id
from website import settings as website_settings
from website.util import api_v2_url, timestamp, web_url_for

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

class GoogleDriveInstitutionsProvider(ExternalProvider):
    name = 'Google Drive in G Suite / Google Workspace'
    short_name = 'googledriveinstitutions'

    client_id = settings.CLIENT_ID
    client_secret = settings.CLIENT_SECRET

    auth_url_base = '{}{}'.format(settings.OAUTH_BASE_URL, 'auth?access_type=offline&approval_prompt=force')
    callback_url = '{}{}'.format(settings.API_BASE_URL, 'oauth2/v3/token')
    auto_refresh_url = callback_url
    refresh_time = settings.REFRESH_TIME
    expiry_time = settings.EXPIRY_TIME

    default_scopes = settings.OAUTH_SCOPE
    _auth_client = GoogleAuthClient()
    _drive_client = GoogleDriveInstitutionsClient()

    def handle_callback(self, response):
        access_token = response['access_token']
        client = self._auth_client
        info = client.userinfo(access_token)
        return {
            'key': access_token,
            'provider_id': info['sub'],
            'display_name': info['name'],
            'profile_url': info.get('profile', None)
        }

    def fetch_access_token(self, force_refresh=False):
        self.refresh_oauth_key(force=force_refresh)
        return self.account.oauth_key

    def auth_callback(self, user, **kwargs):
        # NOTE: "user" must be RdmAddonOption

        try:
            cached_credentials = session.data['oauth_states'][self.short_name]
        except KeyError:
            raise PermissionsError('OAuth flow not recognized.')

        state = request.args.get('state')

        # make sure this is the same user that started the flow
        if cached_credentials.get('state') != state:
            raise PermissionsError('Request token does not match')

        try:
            # Quirk: Similarly to the `oauth2/authorize` endpoint, the `oauth2/access_token`
            #        endpoint of Bitbucket would fail if a not-none or non-empty `redirect_uri`
            #        were provided in the body of the POST request.
            if self.short_name in website_settings.ADDONS_OAUTH_NO_REDIRECT:
                redirect_uri = None
            else:
                redirect_uri = web_url_for(
                    'oauth_callback',
                    service_name=self.short_name,
                    _absolute=True
                )
            response = OAuth2Session(
                self.client_id,
                redirect_uri=redirect_uri,
            ).fetch_token(
                self.callback_url,
                client_secret=self.client_secret,
                code=request.args.get('code'),
            )
        except (MissingTokenError, RequestsHTTPError):
            # raise HTTPError(http_status.HTTP_503_SERVICE_UNAVAILABLE)
            raise HTTPError(503)

        info = self.handle_callback(response)

        if user.external_accounts.filter(
                provider=self.short_name,
                provider_id=info['provider_id']).exists():
            # use existing ExternalAccount and set it to the RdmAddonOption
            pass
        elif user.external_accounts.count() > 0:
            logger.info('Do not add multiple ExternalAccount for googledriveinstitutions.')
            raise HTTPError(400)
        # else: create ExternalAccount and set it to the RdmAddonOption

        result = self._set_external_account(
            user,  # RdmAddonOption
            info
        )
        return result

class UserSettings(BaseOAuthUserSettings):
    oauth_provider = GoogleDriveInstitutionsProvider
    serializer = GoogleDriveInstitutionsSerializer

class NodeSettings(BaseNodeSettings, BaseStorageAddon):
    oauth_provider = GoogleDriveInstitutionsProvider
    provider_name = 'googledriveinstitutions'

    folder_id = models.TextField(null=True, blank=True)
    folder_path = models.TextField(null=True, blank=True)
    serializer = GoogleDriveInstitutionsSerializer
    user_settings = models.ForeignKey(UserSettings, null=True, blank=True, on_delete=models.CASCADE)

    fileaccess_option = models.ForeignKey(
        RdmAddonOption, null=True, blank=True,
        related_name='googledriveinstitutions_fileaccess_option',
        on_delete=models.CASCADE)

    _api = None

    def _get_token(self, name):
        # fileacces_option
        option = getattr(self, '{}_option'.format(name.lower()), None)
        if not option:
            return None
        if name == 'fileaccess' and option.is_allowed is False:
            return None

        # DEBUG_FILEACCESS_TOKEN
        debug = getattr(settings, 'DEBUG_{}_TOKEN'.format(name.upper()), None)
        if debug:
            return debug

        return utils.addon_option_to_token(option)

    @property
    def fileaccess_token(self):
        return self._get_token('fileaccess')

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
        return {'token': self.fileaccess_token}

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

    def set_options(self, f_option, save=False):
        self.fileaccess_option = f_option
        if save:
            self.save()

def init_addon(node, addon_name):
    if node.creator.eppn is None:
        logger.info(u'{} has no ePPN.'.format(node.creator.username))
        return  # disabled
    institution_id = get_institution_id(node.creator)
    if institution_id is None:
        logger.info(u'{} has no institution.'.format(node.creator.username))
        return  # disabled
    fm = utils.get_addon_option(institution_id)
    if fm is None:
        institution = Institution.objects.get(id=institution_id)
        logger.info(u'Institution({}) has no valid oauth keys.'.format(institution.name))
        return  # disabled

    f_option = fm
    f_token = utils.addon_option_to_token(f_option)
    if f_token is None:
        return  # disabled

    addon = node.add_addon(addon_name, auth=Auth(node.creator), log=True)
    addon.set_options(f_option)

    folder = addon.get_folders(folder_id=f_option[KEYNAME_BASE_FOLDER])
    addon.set_folder(folder=folder, auth=Auth(node.creator))


# store values in a short time to detect changed fields
class SyncInfo(object):
    sync_info_dict = {}  # Node.id -> SyncInfo

    def __init__(self):
        self.old_node_title = None
        self.need_to_update_members = False

    @classmethod
    def get(cls, id):
        info = cls.sync_info_dict.get(id)
        if info is None:
            info = SyncInfo()
            cls.sync_info_dict[id] = info
        return info


@receiver(pre_save, sender=Node)
def node_pre_save(sender, instance, **kwargs):
    if instance.is_deleted:
        return

    addon_name = GoogleDriveInstitutionsAddonConfig.short_name
    if addon_name not in website_settings.ADDONS_AVAILABLE_DICT:
        return

    try:
        old_node = Node.objects.get(id=instance.id)
        syncinfo = SyncInfo.get(old_node.id)
        syncinfo.old_node_title = old_node.title
    except Exception:
        pass


@receiver(post_save, sender=Node)
def node_post_save(sender, instance, created, **kwargs):
    if instance.is_deleted:
        DEBUG('instance.is_deleted: True')
        return

    addon_name = GoogleDriveInstitutionsAddonConfig.short_name
    if addon_name not in website_settings.ADDONS_AVAILABLE_DICT:
        return
    DEBUG('created: {}'.format(created))
    if created:
        init_addon(instance, addon_name)
    else:
        ns = instance.get_addon(addon_name)
        DEBUG('ns: {}'.format(ns))
        if ns is None or not ns.complete:  # disabled
            return
        syncinfo = SyncInfo.get(instance.id)
        if ns.owner.title != syncinfo.old_node_title:
            ns.rename_team_folder()
        if syncinfo.need_to_update_members:
            ns.sync_members()
            syncinfo.need_to_update_members = False


@receiver(post_save, sender=Contributor)
@receiver(post_delete, sender=Contributor)
def update_group_members(sender, instance, **kwargs):
    addon_name = GoogleDriveInstitutionsAddonConfig.short_name
    if addon_name not in website_settings.ADDONS_AVAILABLE_DICT:
        return
    node = instance.node
    if node.is_deleted:
        return
    ns = node.get_addon(addon_name)
    if ns is None or not ns.complete:  # disabled
        return
    syncinfo = SyncInfo.get(node.id)
    syncinfo.need_to_update_members = True

# -*- coding: utf-8 -*-
import json

from framework.exceptions import HTTPError
from website.util.client import BaseClient
from addons.googledriveinstitutions import settings


class GoogleAuthClient(BaseClient):

    def userinfo(self, access_token):
        return self._make_request(
            'GET',
            self._build_url(settings.API_BASE_URL, 'oauth2', 'v3', 'userinfo'),
            params={'access_token': access_token},
            expects=(200, ),
            throws=HTTPError(401)
        ).json()


class GoogleDriveInstitutionsClient(BaseClient):

    def __init__(self, access_token=None):
        self.access_token = access_token

    @property
    def _default_headers(self):
        if self.access_token:
            return {'authorization': 'Bearer {}'.format(self.access_token)}
        return {}

    def mkdir(self, base_folder, name):
        self._make_request(
            'POST',
            self.build_url(settings.API_BASE_URL, 'drive', 'v3', 'files'),
            headers={
                'Content-Type': 'application/json',
            },
            data=json.dumps({
                'name': name,
                'parents': [{
                    'id': base_folder
                }],
                'mimeType': 'application/vnd.google-apps.folder',
            }),
            expects=(200, ),
            throws=HTTPError(401),
        )
        return

    def rmdir(self, base_folder, name):
        query = ' and '.join([
            "'{0}' in parents".format(base_folder),
            'trashed = false',
            "mimeType = 'application/vnd.google-apps.folder'",
            "name = '{}'".format(name),
        ])
        res = self._make_request(
            'GET',
            self._build_url(settings.API_BASE_URL, 'drive', 'v3', 'files'),
            params={'q': query, 'fields': 'files(id)'},
            expects=(200, ),
            throws=HTTPError(401)
        )

        rmdir_id = res.json()['files'][0]['id']

        self._make_request(
            'DELETE',
            self.build_url(settings.API_BASE_URL, 'drive', 'v3', 'files', rmdir_id),
            expects=(204, ),
            throws=HTTPError(401)
        )
        return

    def rename(self, base_folder, old_name, new_name):
        query = ' and '.join([
            "'{0}' in parents".format(base_folder),
            'trashed = false',
            "mimeType = 'application/vnd.google-apps.folder'",
            "name = '{}'".format(old_name),
        ])
        res = self._make_request(
            'GET',
            self._build_url(settings.API_BASE_URL, 'drive', 'v3', 'files'),
            params={'q': query, 'fields': 'files(id)'},
            expects=(200, ),
            throws=HTTPError(401)
        )

        old_dir_id = res.json()['files'][0]['id']

        self._make_request(
            'PATCH',
            self.build_url(settings.API_BASE_URL, 'drive', 'v3', 'files', old_dir_id),
            data=json.dumps({
                'name': new_name,
            }),
            expects=(200, ),
            throws=HTTPError(401)
        )
        return

    def rootFolderId(self):
        return self._make_request(
            'GET',
            self._build_url(settings.API_BASE_URL, 'drive', 'v3', 'files', 'root'),
            params={'fields': 'id'},
            expects=(200, ),
            throws=HTTPError(401)
        ).json()['id']

    def folders(self, folder_id='root'):
        query = ' and '.join([
            "'{0}' in parents".format(folder_id),
            'trashed = false',
            "mimeType = 'application/vnd.google-apps.folder'",
        ])
        res = self._make_request(
            'GET',
            self._build_url(settings.API_BASE_URL, 'drive', 'v3', 'files'),
            params={'q': query, 'fields': 'files(id,name)'},
            expects=(200, ),
            throws=HTTPError(401)
        )
        return res.json()['files']

    def get_properties(self, file_id):
        res = self._make_request(
            'GET',
            self._build_url(settings.API_BASE_URL, 'drive', 'v3', 'files', file_id),
            params={'fields': 'properties'},
            expects=(200, ),
            throws=HTTPError(401)
        )
        return res.json()['properties']

    def set_properties(self, file_id, properties):
        res = self._make_request(
            'PATCH',
            self._build_url(settings.API_BASE_URL, 'drive', 'v3', 'files', file_id),
            params={'fields': 'properties'},
            data=json.dumps({
                'properties': properties
            }),
            expects=(200, ),
            throws=HTTPError(401)
        )
        return res.json()['properties']
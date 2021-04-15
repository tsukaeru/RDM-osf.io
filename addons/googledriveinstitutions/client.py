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

    def permission_creat(self, folder_id, extuser):
        res = self._make_request(
            'POST',
            self._build_url(settings.API_BASE_URL, 'drive', 'v3', 'files',
                            folder_id, 'permissions'),
            params={'supportsAllDrives': 'true'},
            headers={
                'Content-Type': 'application/json',
            },
            data=json.dumps({
                'kind': 'drive#permission',
                'emailAddress': extuser,
                'role': 'writer',
                'type': 'user'
            }),
            expects=(200, ),
            throws=HTTPError(401)
        )
        return res.json()

    def permission_list(self, folder_id):
        res = self._make_request(
            'GET',
            self._build_url(settings.API_BASE_URL, 'drive', 'v3', 'files',
                            folder_id, 'permissions'),
            params={'supportsAllDrives': 'true'},
            expects=(200, ),
            throws=HTTPError(401)
        )
        return res.json()['permissions']

    # "getIdForEmail" is a method only available in Google Drive v2 api. 
    # Setting the permission is must know the email's permission id. 
    # So, creat this method and used the "getIdForEmail".
    def getIdForEmail(self, extuser):
        res = self._make_request(
            'GET',
            self._build_url(settings.API_BASE_URL, 'drive', 'v2', 'permissionIds', extuser, ),
            expects=(200, ),
            throws=HTTPError(401)
        )
        return res.json()['id']

    def deletePermissions(self, folder_id, permission_id):
        print(permission_id)
        res = self._make_request(
            'GET',
            self._build_url(settings.API_BASE_URL, 'drive', 'v3', 'files',
                            folder_id, 'permissions', permission_id, ),
            params={'supportsAllDrives': 'true'},
            expects=(200, ),
            throws=HTTPError(401)
        )
        return res.json()

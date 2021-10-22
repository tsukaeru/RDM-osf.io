# -*- coding: utf-8 -*-
from framework.exceptions import HTTPError

from website.util.client import BaseClient
from addons.rushfiles import settings

class RushFilesAuthClient(BaseClient):
    def userinfo(self, access_token, user_main_domain):
        """
        Fetch user profile from https://clientgateway.rushfiles.com/swagger/ui/index#!/User/User_GetUserProfileAlt
        """
        res = self._make_request(
            'GET',
            self._build_url("https://clientgateway." + user_main_domain + "/api/", 'users', 'userprofile'),
            headers={'Authorization':"Bearer " + access_token},
            expects=(200, ),
            throws=HTTPError(401)
        ).json()
        return res["Data"]


class RushFilesClient(BaseClient):
    def __init__(self, access_token=None,user_main_domain=None):
        self.access_token = access_token
        self.user_main_api_base_url = "https://clientgateway." + user_main_domain + "/api/"

    @property
    def _default_headers(self):
        if self.access_token:
            return {'authorization': 'Bearer {}'.format(self.access_token)}
        return {}

    def shares(self,user_id):
        """
        Fetch share list from https://clientgateway.rushfiles.com/swagger/ui/index#!/User/User_GetUserShares
        """
        res = self._make_request(
            'GET',
            self._build_url(self.user_main_api_base_url, 'users', user_id, 'userprofile'),
            headers={'Authorization':"Bearer " + self.access_token},
            expects=(200, ),
            throws=HTTPError(401)
        ).json()
        return res["Data"]

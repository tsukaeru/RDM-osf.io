# -*- coding: utf-8 -*-
from framework.exceptions import HTTPError

from website.util.client import BaseClient
from addons.rushfiles import settings

import sys

class RushFilesAuthClient(BaseClient):
    def userinfo(self, access_token, user_main_domain):
        """
        Fetch user profile from GET /api/client/fullprofile
        """
        res = self._make_request(
            'GET',
            self._build_url("https://clientgateway." + user_main_domain, "api", 'client', 'fullprofile'),
            headers={'Authorization':"Bearer " + access_token},
            params={"tick":1, "api":1,"associationRequired":False},
            expects=(200, )
        ).json()

        return res["Data"]


class RushFilesClient(BaseClient):
    def __init__(self, access_token=None,user_main_domain=None):
        self.access_token = access_token
        self.user_main_api_base_url = "https://clientgateway." + user_main_domain

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
            self._build_url(self.user_main_api_base_url, 'api', 'users', user_id, 'shares'),
            headers={'Authorization':"Bearer " + self.access_token},
            expects=(200, )
        ).json()

        return res["Data"]

# -*- coding: utf-8 -*-
from framework.exceptions import HTTPError

from website.util.client import BaseClient
from addons.rushfiles import settings


class RushFilesClient(BaseClient):

    def __init__(self, access_token=None):
        self.access_token = access_token

    @property
    def _default_headers(self):
        if self.access_token:
            return {'authorization': 'Bearer {}'.format(self.access_token)}
        return {}

    def shares(self):
        raise NotImplementedError

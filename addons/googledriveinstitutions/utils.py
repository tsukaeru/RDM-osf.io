# -*- coding: utf-8 -*-
"""Utility functions for the Google Drive in G Suite / Google Workspace add-on.
"""
import logging
import os
import base64

from osf.models.external import ExternalAccount
from osf.models.rdm_addons import RdmAddonOption
from website.util import timestamp,api_v2_url
from framework.celery_tasks import app as celery_app
from addons.googledriveinstitutions import settings
from addons.googledriveinstitutions.client import GoogleDriveInstitutionsClient

PROVIDER_NAME = 'googledriveinstitutions'

logger = logging.getLogger(__name__)

ENABLE_DEBUG = True

def DEBUG(msg):
    if ENABLE_DEBUG:
        logger.error(u'DEBUG_googledriveinstitutions: {}'.format(msg))

def build_googledriveinstitutions_urls(item, node, path):
    return {
        'fetch': api_v2_url('nodes/{}/addons/googledriveinstitutions/folders/'.format(node._id), params={'path': path}),
        'folders': api_v2_url('nodes/{}/addons/googledriveinstitutions/folders/'.format(node._id), params={'path': path, 'id': item['id']})
    }

def to_hgrid(item, node, path):
    """
    :param item: contents returned from Google Drive API
    :return: results formatted as required for Hgrid display
    """
    path = os.path.join(path, item['name'])

    serialized = {
        'path': path,
        'id': item['id'],
        'kind': 'folder',
        'name': item['name'],
        'addon': 'googledriveinstitutions',
        'urls': build_googledriveinstitutions_urls(item, node, path=path)
    }
    return serialized

def get_timestamp(node_settings, path):
    DEBUG('path: {}'.format(path))
    provider = node_settings.provider
    external_account = provider.account
    # url, username = external_account.provider_id.rsplit(':', 1)
    # password = external_account.oauth_key
    access_token = external_account.oauth_key
    # properties = [
    #     'timestamp',
    #     settings.PROPERTY_KEY_TIMESTAMP_STATUS
    # ]
    # cli = GoogleDriveInstitutionsClient(url, username, password)
    cli = GoogleDriveInstitutionsClient(access_token)
    properties = cli.get_properties(path.identifier)
    if properties is not None:
        # timestamp = cli.get_attribute(res[0], 'timestamp')
        timestamp = properties.get('timestamp')
        if timestamp is None:
            decoded_timestamp = None
        else:
            decoded_timestamp = base64.b64decode(timestamp)
        DEBUG('get timestamp: {}'.format(timestamp))
        # timestamp_status = cli.get_attribute(res[0], settings.PROPERTY_KEY_TIMESTAMP_STATUS)
        timestamp_status = properties.get(settings.PROPERTY_KEY_TIMESTAMP_STATUS)
        try:
            timestamp_status = int(timestamp_status)
        except Exception:
            timestamp_status = None
        DEBUG('get timestamp_status: {}'.format(timestamp_status))
        context = {}
        # context['url'] = url
        # context['username'] = username
        # context['password'] = password
        context['access_token']
        return (decoded_timestamp, timestamp_status, context)
    return (None, None, None)


def set_timestamp(node_settings, path, timestamp_data, timestamp_status, context=None):
    DEBUG('path: {}'.format(path))
    if context is None:
        provider = node_settings.provider
        external_account = provider.account
        # url, username = external_account.provider_id.rsplit(':', 1)
        # password = external_account.oauth_key
        access_token = external_account.oauth_key
    else:
        # url = context['url']
        # username = context['username']
        # password = context['password']
        access_token = context['access_token']
    encoded_timestamp = base64.b64encode(timestamp_data)
    DEBUG('set timestamp: {}'.format(encoded_timestamp))
    properties = {
        'timestamp': encoded_timestamp,
        settings.PROPERTY_KEY_TIMESTAMP_STATUS: str(timestamp_status)
    }
    # cli = GoogleDriveInstitutionsClient(url, username, password)
    cli = GoogleDriveInstitutionsClient(access_token)
    properties = cli.set_properties(path.identifier, properties)
    if properties:
        DEBUG('properties: {}'.format(type(properties)))
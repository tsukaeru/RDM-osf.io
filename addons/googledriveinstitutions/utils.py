# -*- coding: utf-8 -*-
"""Utility functions for the Google Drive in G Suite / Google Workspace add-on.
"""
import logging
import os
import base64

from osf.models.external import ExternalAccount
from osf.models.rdm_addons import RdmAddonOption
from website.util import timestamp, api_v2_url
from framework.celery_tasks import app as celery_app
from addons.googledriveinstitutions import settings
from addons.googledriveinstitutions.client import GoogleDriveInstitutionsClient
from admin.rdm_addons.utils import get_rdm_addon_option

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

def get_addon_option(institution_id, allowed_check=True):
    # avoid "ImportError: cannot import name"
    from addons.googledriveinstitutions.models import GoogleDriveInstitutionsProvider
    fileaccess_addon_option = get_rdm_addon_option(
        institution_id, GoogleDriveInstitutionsProvider.short_name,
        create=False)
    DEBUG('fileaccess_addon_option: {}'.format(fileaccess_addon_option))
    if fileaccess_addon_option is None:
        return None
    if allowed_check and not fileaccess_addon_option.is_allowed:
        DEBUG('allowed_check: {}'.format(allowed_check))
        DEBUG('fileaccess_addon_option.is_allowed: {}'.format(fileaccess_addon_option.is_allowed))
        return None
    return fileaccess_addon_option

def addon_option_to_token(addon_option):
    DEBUG('addon_option: {}'.format(addon_option))
    if not addon_option:
        return None
    if not addon_option.external_accounts.exists():
        DEBUG('addon_option.external_accounts.exists(): {}'.format(
              addon_option.external_accounts.exists()))
        return None
    DEBUG('addon_option.external_accounts.first().oauth_key: {}'.format(
          addon_option.external_accounts.first().oauth_key))
    return addon_option.external_accounts.first().oauth_key
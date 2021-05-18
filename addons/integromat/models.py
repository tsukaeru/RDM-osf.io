# -*- coding: utf-8 -*-
import logging

from django.db import models
from django.contrib.postgres.fields import ArrayField
from osf.models.base import BaseModel
from osf.models.rdm_integromat import RdmWorkflows, RdmWebMeetingApps
from addons.base import exceptions
from addons.base.models import (BaseOAuthNodeSettings, BaseOAuthUserSettings,
                                BaseStorageAddon)
from addons.integromat.serializer import IntegromatSerializer
from addons.integromat.provider import IntegromatProvider
from addons.integromat import SHORT_NAME, FULL_NAME
import addons.integromat.settings as settings

from framework.auth.core import Auth
from osf.models.files import File, Folder, BaseFileNode

logger = logging.getLogger(__name__)


class IntegromatProvider(object):
    name = FULL_NAME
    short_name = SHORT_NAME
    serializer = IntegromatSerializer

    def __init__(self, account=None):
        super(IntegromatProvider, self).__init__()  # this does exactly nothing...
        # provide an unauthenticated session by default
        self.account = account

    def __repr__(self):
        return '<{name}: {status}>'.format(
            name=self.__class__.__name__,
            status=self.account.display_name if self.account else 'anonymous'
        )

class UserSettings(BaseOAuthUserSettings):
    oauth_provider = IntegromatProvider
    serializer = IntegromatSerializer

class NodeSettings(BaseOAuthNodeSettings):
    oauth_provider = IntegromatProvider
    serializer = IntegromatSerializer
    user_settings = models.ForeignKey(UserSettings, null=True, blank=True)
    folder_id = models.TextField(blank=True, null=True)
    folder_name = models.TextField(blank=True, null=True)
    folder_location = models.TextField(blank=True, null=True)

    @property
    def folder_path(self):
        return self.folder_name

    @property
    def display_name(self):
        return u'{0}: {1}'.format(self.config.full_name, self.folder_id)

    @property
    def complete(self):
        return self.has_auth and self.folder_id is not None

    def authorize(self, user_settings, save=False):
        self.user_settings = user_settings
        self.nodelogger.log(action='node_authorized', save=save)

    def clear_settings(self):
        self.folder_id = None
        self.folder_name = None
        self.folder_location = None

    def deauthorize(self, auth=None, log=True):
        """Remove user authorization from this node and log the event."""
        self.clear_settings()
        self.clear_auth()  # Also performs a save

        if log:
            self.nodelogger.log(action='node_deauthorized', save=True)

    def delete(self, save=True):
        self.deauthorize(log=False)
        super(NodeSettings, self).delete(save=save)

    def after_delete(self, user):
        self.deauthorize(Auth(user=user), log=True)

class Attendees(BaseModel):
    id = models.AutoField(primary_key=True)
    user_guid = models.CharField(max_length=128)
    microsoft_teams_mail = models.CharField(max_length=256, blank=True, null=True)
    microsoft_teams_user_name = models.CharField(max_length=256, blank=True, null=True)
    webex_meetings_mail = models.CharField(max_length=256, blank=True, null=True)
    webex_meetings_display_name = models.CharField(max_length=256, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    node_settings = models.ForeignKey(NodeSettings, null=False, blank=False, default=None)

class AllMeetingInformation(BaseModel):
    id = models.AutoField(primary_key=True)
    subject = models.CharField(blank=True, null=True, max_length=254)
    organizer = models.CharField(max_length=254)
    attendees = models.ManyToManyField(Attendees, blank=True, null=True)
    start_datetime = models.DateTimeField(blank=True, null=True)
    end_datetime = models.DateTimeField(blank=True, null=True)
    location = models.CharField(blank=True, null=True, max_length=254)
    content = models.TextField(blank=True, null=True, max_length=10000)
    join_url = models.TextField(max_length=512)
    meetingid = models.TextField(max_length=512)
    app = models.ForeignKey(RdmWebMeetingApps, to_field='id', on_delete=models.CASCADE)
    node_settings = models.ForeignKey(NodeSettings, null=False, blank=False, default=None)

class workflowExecutionMessages(BaseModel):

    id = models.AutoField(primary_key=True)
    notified = models.BooleanField(default=False)
    integromat_msg = models.CharField(blank=True, null=True, max_length=128)
    timestamp = models.CharField(blank=True, null=True, max_length=128)
    node_settings = models.ForeignKey(NodeSettings, null=False, blank=False, default=None)

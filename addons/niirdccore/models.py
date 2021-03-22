# -*- coding: utf-8 -*-
import logging
import json
from celery import Celery
import requests

from django.db import models
from django.db.models import Subquery
from django.db.models.signals import post_save
from django.dispatch import receiver

from osf.models import Contributor, RdmAddonOption, AbstractNode
from osf.models.node import Node

from website.settings import CeleryConfig
from website import util

from . import settings
from . import SHORT_NAME
from addons.base.models import BaseNodeSettings
from website import settings as ws_settings

import addons

logger = logging.getLogger(__name__)

class NodeSettings(BaseNodeSettings):
    """
    プロジェクトにアタッチされたアドオンに関するモデルを定義する。
    """
    dmp_id = models.TextField(blank=True, null=True)
    dmr_api_key = models.TextField(blank=True, null=True)

    # 非同期処理のための変数を定義
    app = Celery()
    app.config_from_object(CeleryConfig)

    def set_dmp_id(self, dmp_id):
        self.dmp_id = dmp_id
        self.save()

    def get_dmp_id(self):
        return self.dmp_id

    def set_dmr_api_key(self, dmr_api_key):
        self.dmr_api_key = dmr_api_key
        self.save()

    def get_dmr_api_key(self):
        return self.dmr_api_key

    @receiver(post_save, sender=Node)
    def add_niirdccore_addon(sender, instance, created, **kwargs):
        if SHORT_NAME not in ws_settings.ADDONS_AVAILABLE_DICT:
            return

        if instance.has_addon(SHORT_NAME):
            # add済みの場合は終了
            return
        # 所属機関によるアドオン追加判定は、adminコンテナの起動が可能になるまでコメントアウトする
        # inst_ids = instance.affiliated_institutions.values('id')
        # addon_option = RdmAddonOption.objects.filter(
        #     provider=SHORT_NAME,
        #     institution_id__in=Subquery(inst_ids),
        #     management_node__isnull=False,
        #     is_allowed=True
        # ).first()
        # if addon_option is None:
        #     return
        # if addon_option.organizational_node is not None and \
        #         not addon_option.organizational_node.is_contributor(instance.creator):
        #     return

        instance.add_addon(SHORT_NAME, auth=None, log=False)

    # DMP情報モニタリング
    @receiver(post_save, sender=Node)
    def node_monitoring(sender, instance, created, **kwargs):
        if SHORT_NAME not in ws_settings.ADDONS_AVAILABLE_DICT:
            return

        sender_node = instance.get_addon(name=SHORT_NAME)
        if sender_node == None:
            return

        sender_dmp_id = sender_node.get_dmp_id()
        if sender_dmp_id == None:
            return

        # DMP更新タスク発行
        NodeSettings.dmp_update(node=instance)

    # DMPの非同期更新処理
    @app.task
    def dmp_update(node):
        # fetch addon data
        json_open = open('addons.json', 'r')
        addons_json = json.load(json_open)

        node_dmp_id = node.get_addon(SHORT_NAME).get_dmp_id()

        addon_list = []
        for addon in node.get_addons():
            addon_apps = eval('addons.' + addon.short_name).default_app_config

            addon_dict = {
                "type": "addon",
                "id": addon.short_name,
                "attributes": {
                    "name": eval(addon_apps).full_name,
                    "url": addons_json.get('addons_url').get(addon.short_name, ''),
                    "description": addons_json.get('addons_description').get(addon.short_name, ''),
                    "categories": eval(addon_apps).categories
                }
            }
            if addon.short_name == addons.jupyterhub.apps.JupyterhubAddonAppConfig.short_name:
                addon_dict['attributes']['services'] = \
                    [{'name': name, 'base_url': url} for name, url in addon.get_services()+ addons.jupyterhub.settings.SERVICES]

            addon_list.append(addon_dict)

        contributor_list = []
        for contributor in node.contributors:
            contributor_dict = {
                "type": contributor.settings_type,
                "id": contributor._id,
                "attributes": {
                    "family_name": contributor.family_name,
                    "given_name": contributor.given_name,
                    "middle_names": contributor.middle_names,
                    "full_name": contributor.fullname,
                    "date_registered": str(contributor.date_registered)
                },
                "links": {
                    "self": util.api_v2_url('/users/' + contributor._id),
                    "href": ws_settings.DOMAIN + '/' + contributor._id
                }
            }
            contributor_list.append(contributor_dict)

        request_body = {
            "data": {
                "title": node.title,
                "addons": addon_list,
                "contributors": contributor_list,

                "links": {
                    "self": util.api_v2_url('/nodes/' + node._id),
                    "href": ws_settings.DOMAIN + '/' + node._id
                }
            }
        }

        # DMP更新リクエスト
        dmr_url = settings.DMR_URL + '/v1/dmp/' + node_dmp_id

        access_token = node.get_addon(SHORT_NAME).get_dmr_api_key()
        headers = {'Authorization': 'Bearer ' + access_token}
        requests.put(dmr_url, headers=headers, json=request_body)

class AddonList(BaseNodeSettings):
    """
    送信先アドオンリストに関するモデルを定義する。
    """
    owner    = models.ForeignKey("NodeSettings", null=True, blank=True, related_name="node")
    node_id = models.CharField(max_length=100, blank=True)
    addon_id = models.CharField(max_length=50, blank=True)
    callback = models.CharField(max_length=100, blank=True)

    def get_owner(self):
        return self.owner

    def set_owner(self, owner):
        self.owner = owner
        self.save()

    def get_node_id(self):
        return self.node_id

    def set_node_id(self, node_id):
        self.node_id = node_id
        self.save()

    def get_addon_id(self):
        return self.addon_id

    def set_addon_id(self, addon_id):
        self.addon_id = addon_id
        self.save()

    def get_callback(self):
        return self.callback

    def set_callback(self, callback):
        self.callback = callback
        self.save()

# -*- coding: utf-8 -*-
from rest_framework import status as http_status
from flask import request
from django.db.models import Subquery
import logging
import requests

from . import SHORT_NAME
from . import settings
from framework.exceptions import HTTPError
from website.project.decorators import (
    must_be_valid_project,
    must_have_permission,
    must_have_addon,
)
from website.ember_osf_web.views import use_ember_app
from addons.jupyterhub.apps import JupyterhubAddonAppConfig
from addons.niirdccore.models import AddonList

from addons import *
from addons.jupyterhub.models import NodeSettings

logger = logging.getLogger(__name__)

@must_be_valid_project
@must_have_permission('admin')
@must_have_addon(SHORT_NAME, 'node')
def niirdccore_set_config(**kwargs):

    node = kwargs['node'] or kwargs['project']
    addon = node.get_addon(SHORT_NAME)

    try:
        dmp_id = request.json['dmp']['redboxOid']
        dmp_metadata = request.json['dmp']['metadata']

        # fetch API key
        dmr_api_key = request.json['dmr_api_key']
    except KeyError:
        raise HTTPError(http_status.HTTP_400_BAD_REQUEST)

    # save dmp_id, API key
    addon.set_dmp_id(dmp_id)
    addon.set_dmr_api_key(dmr_api_key)

    # provisioning
    dataAnalysisResources = dmp_metadata.get("vivo:Dataset_redbox:DataAnalysisResources")

    if dataAnalysisResources:
        try:
            typeName = dataAnalysisResources["type"]
            serviceName = dataAnalysisResources["name"]
            baseUrl = dataAnalysisResources["url"]
        except KeyError:
            raise HTTPError(http_status.HTTP_400_BAD_REQUEST)

        if typeName == JupyterhubAddonAppConfig.full_name \
            or typeName ==  JupyterhubAddonAppConfig.short_name:

            # add jupyterHub
            node.add_addon(JupyterhubAddonAppConfig.short_name, auth=None, log=False)
            jupyterHub = node.get_addon(JupyterhubAddonAppConfig.short_name)
            jupyterHub.set_services([(serviceName, baseUrl)])

            return {"result": "jupyterhub added"}

    return {"result": "jupyterhub none"}

@must_be_valid_project
@must_have_permission('admin')
@must_have_addon(SHORT_NAME, 'node')
def niirdccore_get_dmp_info(**kwargs):
    node = kwargs['node'] or kwargs['project']
    addon = node.get_addon(SHORT_NAME)

    dmp_id = addon.get_dmp_id()

    if dmp_id is None:
        raise HTTPError(http_status.HTTP_410_GONE)

    url = settings.DMR_URL + '/v1/dmp/' + str(dmp_id)
    headers = {'Authorization': 'Bearer ' + addon.get_dmr_api_key()}
    response = requests.get(url, headers=headers)

    try:
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error("Failed to post/put request to DMR, error message: " + str(e))
        raise e

    data = response.json()

    return {'data': {'id': node._id, 'type': 'dmp-status',
                    'attributes': data['dmp']}
            }

@must_be_valid_project
@must_have_permission('admin')
@must_have_addon(SHORT_NAME, 'node')
def niirdccore_update_dmp_info(**kwargs):
    node = kwargs['node'] or kwargs['project']
    addon = node.get_addon(SHORT_NAME)
    dmp_id = addon.get_dmp_id()

    if dmp_id is None:
        raise HTTPError(http_status.HTTP_410_GONE)
    
    # update/create dataset
    try: 
        recv_data = request.json['data']['attributes']
        dataset = recv_data['dataset'][0]
        dataset_is_new = dataset['dataset_is_new']
        dataset_id = dataset['dataset_id']['identifier']
    except KeyError:
        raise HTTPError(http_status.HTTP_400_BAD_REQUEST)

    dataset.pop('dataset_is_new')
    send_data = {'data': dataset}

    headers = {'Authorization': 'Bearer ' + addon.get_dmr_api_key()}

    if dataset_is_new:
        # create dataset
        send_data['data']['dmp_id'] = {'identifier': dmp_id, 'type': 'other'}
        url = settings.DMR_URL + '/v1/dataset/metadata'
        response = requests.post(url, json=send_data, headers=headers)        
    else:
        # update dataset
        url = settings.DMR_URL + '/v1/dataset/{}/metadata'.format(str(dataset_id))
        response = requests.put(url, json=send_data, headers=headers)
    try:
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error("Failed to post/put request to DMR, error message: " + str(e)) 
        raise e

    # get updated dmp
    url = settings.DMR_URL + '/v1/dmp/' + str(dmp_id)
    response = requests.get(url, headers=headers)
    try:
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error("Failed to get request to DMR, error message: " + str(e))
        raise e

    data = response.json()

    return {'data': {'id': node._id, 'type': 'dmp-status',
                    'attributes': data['dmp']}
            }

@must_be_valid_project
@must_have_addon(SHORT_NAME, 'node')
def project_niirdccore(**kwargs):
    return use_ember_app()

@must_be_valid_project
@must_have_permission('admin')
@must_have_addon(SHORT_NAME, 'node')
def niirdccore_apply_dmp_subscribe(**kwargs):
    node = kwargs['node']
    addon = node.get_addon(SHORT_NAME)
    addon_list = AddonList()

    addon_list.set_node_id(node._id)
    addon_list.set_addon_id(kwargs['addon_id'])
    addon_list.set_callback(kwargs['callback'])
    addon_list.set_owner(node.get_addon(SHORT_NAME))

    return

@must_be_valid_project
@must_have_permission('admin')
@must_have_addon(SHORT_NAME, 'node')
def niirdccore_dmp_notification(**kwargs):
    node = kwargs['node']

    # コールバック関数を呼び出す関数
    def _notification_handler(func, **kwargs):
        return func(**kwargs)

    # リクエストボディ取得
    try:
        dmp_record = request.json['dmp']
    except KeyError:
        raise HTTPError(http_status.HTTP_400_BAD_REQUEST)

    addon_list = AddonList.objects.filter(node_id=node._id)

    for addon in addon_list:
        # デコレータ対策のため、nodeも引数に含める
        _notification_handler(
            func=eval(addon.callback),
            node=node,
            dmp_record=dmp_record)

    return

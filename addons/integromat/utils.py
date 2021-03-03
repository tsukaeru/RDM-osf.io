# -*- coding: utf-8 -*-

from addons.integromat.apps import IntegromatAddonConfig

logger = logging.getLogger(__name__)

def serialize_integromat_widget(node):
    iqbrims = node.get_addon('integromat')
    ret = {
        'complete': True,
        'include': False,
        'can_expand': True,
    }
    ret.update(iqbrims.config.to_json())
    return ret

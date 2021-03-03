# -*- coding: utf-8 -*-
"""Routes for the integromat addon.
"""

from framework.routing import Rule, json_renderer
from website.routes import notemplate

from addons.integromat import views

TEMPLATE_DIR = './addons/integromat/templates/'

# HTML endpoints
page_routes = {

    'rules': [

        # Home (Base) | GET
        Rule(
            [
                '/<pid>/integromat',
                '/<pid>/node/<nid>/integromat',
            ],
            'get',
            views.project_integromat,
            notemplate
        ),

    ]
}

# JSON endpoints
api_routes = {
    'rules': [

        Rule(
            '/settings/integromat/',
            'get',
            views.integromat_user_config_get,
            json_renderer,
        ),

        Rule(
            '/settings/integromat/accounts/',
            'post',
            views.integromat_add_user_account,
            json_renderer,
        ),

        Rule(
            [
                '/settings/integromat/accounts/',
            ],
            'get',
            views.integromat_account_list,
            json_renderer,
        ),

        Rule(
            [
                '/project/<pid>/integromat/settings/',
                '/project/<pid>/node/<nid>/integromat/settings/'
            ],
            'get',
            views.integromat_get_config,
            json_renderer,
        ),

        Rule(
            [
                '/project/<pid>/integromat/settings/',
                '/project/<pid>/node/<nid>/integromat/settings/'
            ],
            'put',
            views.integromat_set_config,
            json_renderer,
        ),

        Rule(
            [
                '/project/<pid>/integromat/user_auth/',
                '/project/<pid>/node/<nid>/integromat/user_auth/'
            ],
            'put',
            views.integromat_import_auth,
            json_renderer,
        ),

        Rule(
            [
                '/project/<pid>/integromat/user_auth/',
                '/project/<pid>/node/<nid>/integromat/user_auth/'
            ],
            'delete',
            views.integromat_deauthorize_node,
            json_renderer,
        ),
        #route for Integromat action
        Rule(
            '/integromat/integromat_api_call',
            'post',
            views.integromat_api_call,
            notemplate,
        ),

        Rule(
            '/project/<pid>/integromat/add_microsoft_teams_user',
            'post',
            views.integromat_add_microsoft_teams_user,
            json_renderer,
        ),

        Rule(
            '/project/<pid>/integromat/delete_microsoft_teams_user',
            'post',
            views.integromat_delete_microsoft_teams_user,
            json_renderer,
        ),

        Rule(
            '/integromat/create_meeting_info',
            'post',
            views.integromat_create_meeting_info,
            json_renderer,
        ),

        Rule(
            '/integromat/update_meeting_info',
            'post',
            views.integromat_update_meeting_info,
            json_renderer,
        ),

        Rule(
            '/integromat/delete_meeting_info',
            'post',
            views.integromat_delete_meeting_info,
            json_renderer,
        ),

        Rule(
            '/integromat/start_scenario',
            'post',
            views.integromat_start_scenario,
            json_renderer,
        ),

        Rule(
            '/integromat/requestNextMessages',
            'post',
            views.integromat_req_next_msg,
            json_renderer,
        ),

        Rule(
            '/integromat/info_msg',
            'post',
            views.integromat_info_msg,
            json_renderer,
        ),

        Rule(
            '/integromat/error_msg',
            'post',
            views.integromat_error_msg,
            json_renderer,
        ),

        Rule(
            [
                '/project/<pid>/integromat/get_meetings',
                '/project/<pid>/node/<nid>/integromat/get_meetings',
            ],
            'get',
            views.integromat_get_meetings,
            json_renderer,
        ),

        Rule(
            [
                '/project/<pid>/integromat/buckets/',
                '/project/<pid>/node/<nid>/integromat/buckets/',
            ],
            'get',
            views.integromat_folder_list,
            json_renderer,
        ),
        Rule(
            [
                '/project/<pid>/integromat/newbucket/',
                '/project/<pid>/node/<nid>/integromat/newbucket/',
            ],
            'post',
            views.integromat_create_bucket,
            json_renderer
        ),

        # ember: ここから
        Rule([
            '/project/<pid>/integromat/config',
            '/project/<pid>/node/<nid>/integromat/config',
        ], 'get', views.integromat_get_config_ember, json_renderer),
        # ember: ここまで

    ],
    'prefix': '/api/v1'
}

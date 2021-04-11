from addons.base.apps import BaseAddonAppConfig, generic_root_folder
from addons.googledriveinstitutions.settings import MAX_UPLOAD_SIZE
from website.util import rubeus


def googledriveinstitutions_root(addon_config, node_settings, auth, **kwargs):
    from addons.osfstorage.models import Region

    node = node_settings.owner
    institution = node_settings.addon_option.institution
    if Region.objects.filter(_id=institution._id).exists():
        region = Region.objects.get(_id=institution._id)
        if region:
            node_settings.region = region
    root = rubeus.build_addon_root(
        node_settings=node_settings,
        name='',
        permissions=auth,
        user=auth.user,
        nodeUrl=node.url,
        nodeApiUrl=node.api_url,
    )
    return [root]


class GoogleDriveInstitutionsAddonConfig(BaseAddonAppConfig):

    name = 'addons.googledriveinstitutions'
    label = 'addons_googledriveinstitutions'
    full_name = 'Google Drive in G Suite / Google Workspace'
    short_name = 'googledriveinstitutions'
    owners = ['user', 'node']
    configs = ['accounts', 'node']
    categories = ['storage']
    has_hgrid_files = True
    max_file_size = MAX_UPLOAD_SIZE

    get_hgrid_data = googledriveinstitutions_root

    FOLDER_SELECTED = 'googledriveinstitutions_folder_selected'
    NODE_AUTHORIZED = 'googledriveinstitutions_node_authorized'
    NODE_DEAUTHORIZED = 'googledriveinstitutions_node_deauthorized'

    actions = (FOLDER_SELECTED, NODE_AUTHORIZED, NODE_DEAUTHORIZED, )

    # default value for RdmAddonOption.is_allowed for GRDM Admin
    is_allowed_default = False 
    for_institutions = True

    @property
    def routes(self):
        from . import routes
        return [routes.auth_routes, routes.api_routes]

    @property
    def user_settings(self):
        return self.get_model('UserSettings')

    @property
    def node_settings(self):
        return self.get_model('NodeSettings')

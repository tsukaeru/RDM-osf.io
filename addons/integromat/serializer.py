import logging

from addons.base.serializer import StorageAddonSerializer
from addons.integromat import SHORT_NAME
from addons.integromat import settings
from website.util import web_url_for

logger = logging.getLogger(__name__)

class IntegromatSerializer(StorageAddonSerializer):
    addon_short_name = SHORT_NAME

    REQUIRED_URLS = []

    @property
    def addon_serialized_urls(self):
        logger.info('addon_serialized_urls start')
        node = self.node_settings.owner
        user_settings = self.node_settings.user_settings or self.user_settings

        result = {
            'accounts': node.api_url_for('{}_account_list'.format(SHORT_NAME)),
            'importAuth': node.api_url_for('{}_import_auth'.format(SHORT_NAME)),
            'create': node.api_url_for('{}_add_user_account'.format(SHORT_NAME)),
            'deauthorize': node.api_url_for('{}_deauthorize_node'.format(SHORT_NAME)),
            'config': node.api_url_for('{}_set_config'.format(SHORT_NAME)),
            'add_microsoft_teams_user': node.api_url_for('{}_add_microsoft_teams_user'.format(SHORT_NAME)),
            'delete_microsoft_teams_user': node.api_url_for('{}_delete_microsoft_teams_user'.format(SHORT_NAME)),
        }
        if user_settings:
            result['owner'] = web_url_for('profile_view_id',
                                          uid=user_settings.owner._id)

        logger.info('addon_serialized_urls end')

        return result

    def serialized_folder(self, node_settings):
        logger.info('serialized_folder start')
        logger.info('serialized_folder end')
        return {
            'path': node_settings.folder_id,
            'name': node_settings.folder_name
        }

    def credentials_are_valid(self, user_settings, client=None):
        logger.info('credentials_are_valid start')

        if user_settings:
            logger.info('credentials_are_valid end Ture')
            return True
        '''
            for account in user_settings.external_accounts.all():
                if utils.can_list(settings.HOST,
                                  account.oauth_key, account.oauth_secret):
                    return True
        '''
        logger.info('credentials_are_valid False')
        return False

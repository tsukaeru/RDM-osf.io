# -*- coding: utf-8 -*-
from rest_framework import status as http_status

from boto.exception import S3ResponseError
import mock
from nose.tools import (assert_equal, assert_equals,
    assert_true, assert_in, assert_false)
import pytest

from framework.auth import Auth
from tests.base import OsfTestCase, get_default_metaschema
from osf_tests.factories import ProjectFactory, AuthUserFactory, DraftRegistrationFactory, InstitutionFactory

from addons.base.tests.views import (
    OAuthAddonConfigViewsTestCaseMixin
)
from addons.integromat.tests.utils import IntegromatAddonTestCase
from addons.integromat.utils import validate_bucket_name
import addons.integromat.settings as integromat_settings
from website.util import api_url_for
from admin.rdm_addons.utils import get_rdm_addon_option

pytestmark = pytest.mark.django_db

class TestIntegromatViews(IntegromatAddonTestCase, OAuthAddonConfigViewsTestCaseMixin, OsfTestCase):
    def setUp(self):
        self.mock_uid = mock.patch('addons.integromat.views.authIntegromat')
        self.mock_uid.return_value = {'id': '1234567890', 'name': 'integromat.user'}
        self.mock_uid.start()
        super(TestIntegromatViews, self).setUp()

    def tearDown(self):
        self.mock_uid.stop()
        super(TestIntegromatViews, self).tearDown()

    def test_integromat_settings_input_empty_keys(self):
        url = self.project.api_url_for('integromat_add_user_account')
        rv = self.app.post_json(url, {
            'access_key': '',
        }, auth=self.user.auth, expect_errors=True)
        assert_equals(rv.status_int, http_status.HTTP_400_BAD_REQUEST)
        assert_in('All the fields above are required.', rv.body.decode())

    def test_integromat_settings_input_empty_access_key(self):
        url = self.project.api_url_for('integromat_add_user_account')
        rv = self.app.post_json(url, {
            'access_key': '',
        }, auth=self.user.auth, expect_errors=True)
        assert_equals(rv.status_int, http_status.HTTP_400_BAD_REQUEST)
        assert_in('All the fields above are required.', rv.body.decode())

    def test_integromat_settings_rdm_addons_denied(self):
        institution = InstitutionFactory()
        self.user.affiliated_institutions.add(institution)
        self.user.save()
        rdm_addon_option = get_rdm_addon_option(institution.id, self.ADDON_SHORT_NAME)
        rdm_addon_option.is_allowed = False
        rdm_addon_option.save()
        url = self.project.api_url_for('integromat_add_user_account')
        rv = self.app.post_json(url,{
            'access_key': 'aldkjf',
        }, auth=self.user.auth, expect_errors=True)
        assert_equal(rv.status_int, http_status.HTTP_403_FORBIDDEN)
        assert_in('You are prohibited from using this add-on.', rv.body.decode())

    def test_integromat_remove_node_settings_owner(self):
        url = self.node_settings.owner.api_url_for('integromat_deauthorize_node')
        self.app.delete(url, auth=self.user.auth)
        result = self.Serializer().serialize_settings(node_settings=self.node_settings, current_user=self.user)
        assert_equal(result['nodeHasAuth'], False)

    def test_integromat_remove_node_settings_unauthorized(self):
        url = self.node_settings.owner.api_url_for('integromat_deauthorize_node')
        ret = self.app.delete(url, auth=None, expect_errors=True)

        assert_equal(ret.status_code, 401)

    def test_integromat_get_node_settings_owner(self):
        self.node_settings.set_auth(self.external_account, self.user)
        self.node_settings.folder_id = 'bucket'
        self.node_settings.save()
        url = self.node_settings.owner.api_url_for('integromat_get_config')
        res = self.app.get(url, auth=self.user.auth)

        result = res.json['result']
        assert_equal(result['nodeHasAuth'], True)
        assert_equal(result['userIsOwner'], True)
        assert_equal(result['folder']['path'], self.node_settings.folder_id)

    def test_integromat_get_node_settings_unauthorized(self):
        url = self.node_settings.owner.api_url_for('integromat_get_config')
        unauthorized = AuthUserFactory()
        ret = self.app.get(url, auth=unauthorized.auth, expect_errors=True)

        assert_equal(ret.status_code, 403)

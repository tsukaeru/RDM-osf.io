from django.test import RequestFactory
from nose import tools as nt
from datetime import datetime, timedelta

from tests.base import AdminTestCase
from tests.factories import CommentFactory, AuthUserFactory, ProjectFactory
from admin_tests.utilities import setup_view

from admin.spam.views import SpamList, UserSpamList


class TestSpamListView(AdminTestCase):
    def setUp(self):
        super(TestSpamListView, self).setUp()
        self.project = ProjectFactory(is_public=True)
        self.user_1 = AuthUserFactory()
        self.user_2 = AuthUserFactory()
        self.project.add_contributor(self.user_1)
        self.project.add_contributor(self.user_2)
        self.project.save()
        self.user_1.save()
        self.user_2.save()
        date = datetime.utcnow()
        self.comment_1 = CommentFactory(node=self.project, user=self.user_1)
        self.comment_2 = CommentFactory(node=self.project, user=self.user_1)
        self.comment_3 = CommentFactory(node=self.project, user=self.user_1)
        self.comment_4 = CommentFactory(node=self.project, user=self.user_1)
        self.comment_5 = CommentFactory(node=self.project, user=self.user_2)
        self.comment_6 = CommentFactory(node=self.project, user=self.user_2)
        self.comment_1.report_abuse(
            user=self.user_2,
            save=True,
            category='spam',
            date=date - timedelta(seconds=5)
        )
        self.comment_2.report_abuse(
            user=self.user_2,
            save=True,
            category='spam',
            date=date - timedelta(seconds=4)
        )
        self.comment_3.report_abuse(
            user=self.user_2,
            save=True,
            category='spam',
            date=date - timedelta(seconds=3)
        )
        self.comment_4.report_abuse(
            user=self.user_2,
            save=True,
            category='spam',
            date=date - timedelta(seconds=2)
        )
        self.comment_5.report_abuse(
            user=self.user_1,
            save=True,
            category='spam',
            date=date - timedelta(seconds=1)
        )
        self.comment_6.report_abuse(user=self.user_1, save=True,
                                    category='spam')

    def test_get_spam(self):
        guid = self.user_1._id
        request = RequestFactory().get('/fake_path')
        view = SpamList()
        view = setup_view(view, request, user_id=guid)
        res = list(view.get_queryset())
        nt.assert_equal(len(res), 6)
        response_list = [r._id for r in res]
        should_be = [
            self.comment_6._id,
            self.comment_5._id,
            self.comment_4._id,
            self.comment_3._id,
            self.comment_2._id,
            self.comment_1._id
        ]
        nt.assert_list_equal(should_be, response_list)


class TestUserSpamListView(AdminTestCase):
    def setUp(self):
        super(TestUserSpamListView, self).setUp()
        self.project = ProjectFactory(is_public=True)
        self.user_1 = AuthUserFactory()
        self.user_2 = AuthUserFactory()
        self.project.add_contributor(self.user_1)
        self.project.add_contributor(self.user_2)
        self.project.save()
        self.user_1.save()
        self.user_2.save()
        self.comment_1 = CommentFactory(node=self.project, user=self.user_1)
        self.comment_2 = CommentFactory(node=self.project, user=self.user_1)
        self.comment_3 = CommentFactory(node=self.project, user=self.user_1)
        self.comment_4 = CommentFactory(node=self.project, user=self.user_1)
        self.comment_5 = CommentFactory(node=self.project, user=self.user_2)
        self.comment_6 = CommentFactory(node=self.project, user=self.user_2)
        self.comment_1.report_abuse(user=self.user_2, save=True,
                                    category='spam')
        self.comment_2.report_abuse(user=self.user_2, save=True,
                                    category='spam')
        self.comment_3.report_abuse(user=self.user_2, save=True,
                                    category='spam')
        self.comment_4.report_abuse(user=self.user_2, save=True,
                                    category='spam')
        self.comment_5.report_abuse(user=self.user_1, save=True,
                                    category='spam')
        self.comment_6.report_abuse(user=self.user_1, save=True,
                                    category='spam')

    def test_get_user_spam(self):
        guid = self.user_1._id
        request = RequestFactory().get('/fake_path')
        view = UserSpamList()
        view = setup_view(view, request, user_id=guid)
        res = list(view.get_queryset())
        nt.assert_equal(len(res), 4)

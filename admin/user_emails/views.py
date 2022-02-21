from __future__ import unicode_literals

import logging

from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.defaults import page_not_found, permission_denied
from django.views.generic import FormView
from django.views.generic import ListView
from rest_framework import status as http_status

from admin.base.views import GuidView
from admin.rdm.utils import RdmPermissionMixin
from admin.user_emails.forms import UserEmailsSearchForm
from framework.exceptions import HTTPError
from osf.models.user import OSFUser
from website import mailchimp_utils
from website import mails
from website import settings

logger = logging.getLogger(__name__)


class UserEmailsFormView(RdmPermissionMixin, FormView):
    template_name = 'user_emails/search.html'
    object_type = 'osfuser'
    permission_required = ()
    raise_exception = True
    form_class = UserEmailsSearchForm

    def __init__(self, *args, **kwargs):
        self.redirect_url = reverse('user-emails:search')
        super(UserEmailsFormView, self).__init__(*args, **kwargs)

    def form_valid(self, form):
        guid = form.cleaned_data['guid']
        name = form.cleaned_data['name']
        email = form.cleaned_data['email']
        request_user = self.request.user

        if guid or email:
            if email:
                try:
                    users_query = OSFUser.objects.filter(is_active=True, is_registered=True)
                    users_query = users_query.filter(Q(username=email) | Q(emails__address=email))
                    if self.is_admin:
                        now_institutions_id = list(request_user.affiliated_institutions.all().values_list('pk', flat=True))
                        users_query = users_query.filter(affiliated_institutions__in=now_institutions_id)
                    user = users_query.distinct('id').get()
                    guid = user.guids.first()._id
                except OSFUser.DoesNotExist:
                    msg = 'User with email address {} not found.'.format(email)
                    return page_not_found(self.request, AttributeError(msg))
                except OSFUser.MultipleObjectsReturned:
                    msg = 'Multiple users with email address {} found, please notify DevOps.'.format(email)
                    return page_not_found(self.request, AttributeError(msg))
            self.redirect_url = reverse('user-emails:user', kwargs={'guid': guid})
        elif name:
            self.redirect_url = reverse('user-emails:search_list', kwargs={'name': name})

        return super(UserEmailsFormView, self).form_valid(form)

    @property
    def success_url(self):
        return self.redirect_url


class UserEmailsSearchList(RdmPermissionMixin, ListView):
    template_name = 'user_emails/user_list.html'
    permission_required = 'osf.view_osfuser'
    raise_exception = True
    form_class = UserEmailsSearchForm
    paginate_by = 25

    def get_queryset(self):
        keyword = self.kwargs['name']
        request_user = self.request.user

        if not keyword:
            raise HTTPError(http_status.HTTP_400_BAD_REQUEST)
        users_query = OSFUser.objects.filter(is_active=True, is_registered=True)
        users_query = users_query.filter(fullname__icontains=keyword)
        if self.is_admin:
            now_institutions_id = list(request_user.affiliated_institutions.all().values_list('pk', flat=True))
            users_query = users_query.filter(affiliated_institutions__in=now_institutions_id)
        users_query = users_query.order_by('fullname').only(
            'guids', 'fullname', 'username', 'date_confirmed', 'date_disabled'
        )
        return users_query

    def get_context_data(self, **kwargs):
        users = self.get_queryset()
        page_size = self.get_paginate_by(users)
        paginator, page, query_set, is_paginated = self.paginate_queryset(users, page_size)
        kwargs['page'] = page
        kwargs['users'] = [{
            'name': user.fullname,
            'username': user.username,
            'id': user.guids.first()._id,
            'confirmed': user.date_confirmed,
            'disabled': user.date_disabled if user.is_disabled else None
        } for user in query_set]
        return super(UserEmailsSearchList, self).get_context_data(**kwargs)


class UserEmailsView(RdmPermissionMixin, GuidView):
    template_name = 'user_emails/user_emails.html'
    context_object_name = 'user'
    permission_required = 'osf.view_osfuser'
    raise_exception = True

    def get_context_data(self, **kwargs):
        kwargs = super(UserEmailsView, self).get_context_data(**kwargs)
        return kwargs

    def get_object(self, queryset=None):
        request_user = self.request.user
        user = OSFUser.load(self.kwargs.get('guid'))

        if self.is_admin:
            now_institutions_id = list(request_user.affiliated_institutions.all().values_list('pk', flat=True))
            all_institution_users_id = list(OSFUser.objects.filter(affiliated_institutions__in=now_institutions_id).distinct().values_list('pk', flat=True))

            if user.pk not in all_institution_users_id:
                raise HTTPError(http_status.HTTP_403_FORBIDDEN)

        return {
            'username': user.username,
            'name': user.fullname,
            'id': user._id,
            'emails': user.emails.values_list('address', flat=True),
        }


class UserPrimaryEmail(RdmPermissionMixin, View):
    permission_required = 'osf.view_osfuser'
    raise_exception = True

    def post(self, request, *args, **kwargs):
        request_user = self.request.user
        user = OSFUser.load(self.kwargs.get('guid'))
        primary_email = request.POST.get('primary_email')
        username = None

        if self.is_admin:
            now_institutions_id = list(request_user.affiliated_institutions.all().values_list('pk', flat=True))
            all_institution_users_id = list(OSFUser.objects.filter(affiliated_institutions__in=now_institutions_id).distinct().values_list('pk', flat=True))

            if user.pk not in all_institution_users_id:
                # raise HTTPError(http_status.HTTP_403_FORBIDDEN)
                return permission_denied(self.request)

        # Refer to website.profile.views.update_user
        if primary_email:
            primary_email_address = primary_email.strip().lower()
            if primary_email_address not in [each.strip().lower() for each in user.emails.values_list('address', flat=True)]:
                # raise HTTPError(http_status.HTTP_403_FORBIDDEN)
                # return permission_denied(self.request)
                user.emails.create(address=primary_email_address.lower().strip())
            username = primary_email_address

        # make sure the new username has already been confirmed
        if username and username != user.username and user.emails.filter(address=username).exists():

            mails.send_mail(
                user.username,
                mails.PRIMARY_EMAIL_CHANGED,
                user=user,
                new_address=username,
                can_change_preferences=False,
                osf_contact_email=settings.OSF_CONTACT_EMAIL
            )

            # Remove old primary email from subscribed mailing lists
            for list_name, subscription in user.mailchimp_mailing_lists.items():
                if subscription:
                    mailchimp_utils.unsubscribe_mailchimp_async(list_name, user._id, username=user.username)
            user.username = username

        user.save()

        return redirect(reverse('user-emails:user', kwargs={'guid': user._id}))

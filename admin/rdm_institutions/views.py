# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.core import serializers
from django.forms.models import model_to_dict
from django.shortcuts import redirect
from django.http import HttpResponse
from django.views.generic import ListView, DetailView, View, UpdateView, TemplateView
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.core.urlresolvers import reverse, reverse_lazy
from osf.models import Institution, Node
from admin.base import settings
from admin.base.forms import ImportFileForm
from admin.rdm_institutions.forms import InstitutionForm


class InstitutionDisplay(UserPassesTestMixin, DetailView):
    model = Institution
    template_name = 'rdm_institutions/detail.html'
    raise_exception = True

    def test_func(self):
        # user = self.request.user
        # institution_id = self.kwargs.get('institution_id')
        # return user.is_authenticated and user.is_admin
        return True
 
    def get_object(self, queryset=None):
        return Institution.objects.get(id=self.kwargs.get('institution_id'))

    def get_context_data(self, *args, **kwargs):
        institution = self.get_object()
        institution_dict = model_to_dict(institution)
        kwargs.setdefault('page_number', self.request.GET.get('page', '1'))
        kwargs['institution'] = institution_dict
        kwargs['logohost'] = settings.OSF_URL
        fields = institution_dict
        kwargs['change_form'] = InstitutionForm(initial=fields)
        kwargs['import_form'] = ImportFileForm()
        kwargs['node_count'] = institution.nodes.count()

        return kwargs


class InstitutionDetail(UserPassesTestMixin, View):
    raise_exception = True

    def test_func(self):
        # user = self.request.user
        # return user.is_authenticated and user.is_admin
        return True

    def get(self, request, *args, **kwargs):
        user = self.request.user
        institution = user.affiliated_institutions.first()
        kwargs['institution_id'] = institution.id
        view = InstitutionDisplay.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        institution = user.affiliated_institutions.first()
        kwargs['institution_id'] = institution.id
        view = InstitutionChangeForm.as_view()
        return view(request, *args, **kwargs)


class InstitutionChangeForm(UserPassesTestMixin, UpdateView):
    raise_exception = True
    model = Institution
    form_class = InstitutionForm

    def test_func(self):
        # user = self.request.user
        # institution_id = self.kwargs.get('institution_id')
        # return user.is_authenticated and user.is_admin
        return True

    def get_object(self, queryset=None):
        institution_id = self.kwargs.get('institution_id')
        return Institution.objects.get(id=institution_id)

    def get_context_data(self, *args, **kwargs):
        kwargs['import_form'] = ImportFileForm()
        return super(InstitutionChangeForm, self).get_context_data(*args, **kwargs)

    def get_success_url(self, *args, **kwargs):
        return reverse_lazy('rdm_institutions:detail', kwargs={'institution_id': self.kwargs.get('institution_id')})


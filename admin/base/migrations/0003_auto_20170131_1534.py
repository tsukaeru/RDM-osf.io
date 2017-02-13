# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-01-31 21:34
from __future__ import unicode_literals

from django.db.models import Q
from django.db import migrations
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.core.management.sql import emit_post_migrate_signal

import logging

logger = logging.getLogger(__file__)


def get_read_only_permissions():
    return Permission.objects.filter(
        Q(codename='view_node') |
        Q(codename='view_registration') |
        Q(codename='view_user') |
        Q(codename='view_conference') |
        Q(codename='view_spam') |
        Q(codename='view_metrics') |
        Q(codename='view_desk')
    )


def get_admin_permissions():
    return Permission.objects.filter(
        Q(codename='change_node') |
        Q(codename='delete_node') |
        Q(codename='change_user') |
        Q(codename='change_conference') |
        Q(codename='mark_spam')
    )


def get_prereg_admin_permissions():
    return Permission.objects.filter(
        Q(codename='view_prereg') |
        Q(codename='administer_prereg')
    )


def add_group_permissions(*args):
    # this is to make sure that the permissions created in an earlier migration exist!
    emit_post_migrate_signal(2, False, 'default')

    group = Group.objects.get(name='read_only')
    if not group:
        try:
            # Rename nodes_and_users group to read_only which makes more sense
            group = Group.objects.get(name='nodes_and_users')
            group.name = 'read_only'
            group.save()
            logger.info('nodes_and_users renamed to read_only')
        except Group.DoesNotExist:
            group = Group.objects.get_or_create(name='read_only')
            logger.info('read_only group created')

    # Read only for nodes, users, meetings, and spam
    [group.permissions.add(perm) for perm in get_read_only_permissions()]
    group.save()
    logger.info('Node, user, spam and meeting permissions added to read only group')

    # Admin for nodes, users, meetings, and spam - reuse previous osf_admiin group
    admin_group, created = Group.objects.get_or_create(name='osf_admin')
    if created:
        logger.info('admin_user Group created')
    [admin_group.permissions.add(perm) for perm in get_read_only_permissions()]
    [admin_group.permissions.add(perm) for perm in get_admin_permissions()]
    group.save()
    logger.info('Administrator permissions for Node, user, spam and meeting permissions added to admin group')

    prereg_group = Group.objects.get(name='prereg_admin')
    if not prereg_group:
        try:
            # rename prereg group to prereg_admin
            prereg_group = Group.objects.get(name='prereg')
            prereg_group.name = 'prereg_admin'
            prereg_group.save()
            logger.info('prereg renamed to prereg_admin')
        except Group.DoesNotExist:
            prereg_group = Group.objects.create(name='prereg_admin')
            logger.info('read_only group created')

    [prereg_group.permissions.add(perm) for perm in get_prereg_admin_permissions()]
    prereg_group.save()
    logger.info('Prereg read and administer permissions added to the prereg_admin group')

    # Remove superfluous osf_group
    try:
        Group.objects.get(name='osf_group').delete()
    except Group.DoesNotExist:
        pass

    # Add a metrics_only Group for ease in the user registration form
    metrics_group, created = Group.objects.get_or_create(name='metrics_only')
    metrics_permission = Permission.objects.get(codename='view_metrics', content_type__app_label='admin_common_auth')
    metrics_group.permissions.add(metrics_permission)
    metrics_group.save()

    # Add a view_prereg Group for ease in the user registration form
    prereg_view_group, created = Group.objects.get_or_create(name='prereg_view')
    prereg_view_permission = Permission.objects.get(codename='view_prereg', content_type__app_label='admin_common_auth')
    prereg_view_group.permissions.add(prereg_view_permission)
    prereg_view_group.save()


def remove_group_permissions(*args):

    # reverse the naming for nodes_and_users
    group = Group.objects.get(name='read_only')
    [group.permissions.remmove(perm) for perm in get_read_only_permissions()]
    group.name = 'nodes_and_users'
    group.save()

    # remove permissions for osf admin group
    admin_group = Group.objects.get(name='osf_admin')
    [admin_group.permissions.remove(perm) for perm in get_read_only_permissions()]
    [admin_group.permissions.remove(perm) for perm in get_admin_permissions()]
    admin_group.save()

    # reverse the naming for prereg to prereg_admin
    prereg_group = Group.objects.get(name='prereg_admin')
    [prereg_group.permissions.remmove(perm) for perm in get_prereg_admin_permissions()]
    prereg_group.name = 'prereg'
    prereg_group.save()

    # re-create osf_group
    group, created = Group.objects.get_or_create(name='osf_group')
    if created:
        logger.info('osf_group created')

    # remove the new metrics group
    Group.objects.get(name='metrics_only').delete()

    # remove the new prereg view group
    Group.objects.get(name='prereg_view').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('admin_base', '0002_groups'),
        ('admin_common_auth', '0006_auto_20170130_1611')
    ]

    operations = [
        migrations.RunPython(add_group_permissions, remove_group_permissions),
    ]

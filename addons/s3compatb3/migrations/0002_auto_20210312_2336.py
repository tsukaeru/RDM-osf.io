# -*- coding: utf-8 -*-
# Generated by Django 1.11.28 on 2021-03-12 23:36
from __future__ import unicode_literals

from django.db import migrations
import osf.utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('addons_s3compatb3', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='nodesettings',
            new_name='is_deleted',
            old_name='deleted',
        ),
        migrations.RenameField(
            model_name='usersettings',
            new_name='is_deleted',
            old_name='deleted',
        ),
        migrations.AddField(
            model_name='nodesettings',
            name='deleted',
            field=osf.utils.fields.NonNaiveDateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='usersettings',
            name='deleted',
            field=osf.utils.fields.NonNaiveDateTimeField(blank=True, null=True),
        ),
    ]

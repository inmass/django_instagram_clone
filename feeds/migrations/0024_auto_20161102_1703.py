# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-11-02 17:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0023_auto_20161102_1703'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='room',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='feeds.Room'),
        ),
    ]

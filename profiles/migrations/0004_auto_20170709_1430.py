# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-09 13:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0003_auto_20170709_1414'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='client_types',
            field=models.ManyToManyField(to='profiles.ClientType'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='consultation_types',
            field=models.ManyToManyField(to='profiles.ConsultationType'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='counselling_areas',
            field=models.ManyToManyField(to='profiles.CounsellingArea'),
        ),
    ]
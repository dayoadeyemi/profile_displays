# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.postgres.fields import ArrayField
from uuid import uuid4

def empty():
    return []

class Profile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    about_me = models.TextField()
    qualifications = models.TextField()
    counselling_areas = ArrayField(models.CharField(max_length=256), default=empty)
    consultation_types = ArrayField(models.CharField(max_length=256), default=empty)
    fees = models.DecimalField(null=True, decimal_places=2, max_digits=10)
    client_types = ArrayField(models.CharField(max_length=256), default=empty)
    concessions_availible = models.BooleanField(default=False)
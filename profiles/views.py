# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse, Http404

from .models import Profile

def full(request, id):
    try:
        profile = Profile.objects.get(pk=id)
    except Profile.DoesNotExist:
        raise Http404("Profile does not exist")
    return render(request, 'profiles/full.html', {'profile': profile})
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import Profile


def full(request, id):
    try:
        profile = Profile.objects.get(pk=id).presentable()
    except Profile.DoesNotExist:
        raise Http404("Profile does not exist")
    return render(request, 'profiles/full.html', {
        'profile': profile,
    })

def index(request):
    profiles_list = map(lambda p:p.presentable(), Profile.objects.all())
    page = request.GET.get('page', 1)

    paginator = Paginator(profiles_list, 10)
    try:
        profiles = paginator.page(page)
    except PageNotAnInteger:
        profiles = paginator.page(1)
    except EmptyPage:
        profiles = paginator.page(paginator.num_pages)

    return render(request, 'profiles/index.html', {
        'profiles': profiles
    })
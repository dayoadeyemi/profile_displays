# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Func, F, Count, Subquery, OuterRef
from django.db.models.expressions import RawSQL
from django.db.models.aggregates import Sum


from .models import Profile

def annotate_intersection_count(field, values, qs):
    return qs.annotate(**dict([(
            'icount_'+field,
            Func(RawSQL(field+'::varchar[]', ()),
            RawSQL('%s::varchar[]', (map(lambda p:p, values),)),
            function='icount'))]))

def full(request, id):
    try:
        profile = Profile.objects.get(pk=id).presentable()
        get_similar = \
            annotate_intersection_count('keywords', profile.keywords,
            annotate_intersection_count('counselling_areas', profile.counselling_areas,
            annotate_intersection_count('consultation_types', profile.consultation_types,
            annotate_intersection_count('client_types', profile.client_types,
            Profile.objects.exclude(id=id))))) \
            .annotate(
                similarity=Func(F('icount_keywords'),
                    F('icount_counselling_areas'), 
                    F('icount_consultation_types'),
                    F('icount_client_types'), function='sim_sum')
            ) \
            .order_by('-similarity')

        print  get_similar.query
        
        show_similar = False if request.GET.get('no_similar', False) else True

        print 'show_similar', show_similar
        
        simliarProfiles = map(lambda p:p.presentable(), get_similar[:10])
    except Profile.DoesNotExist:
        raise Http404("Profile does not exist")
    return render(request, 'profiles/full.html', {
        'profile': profile,
        'simliarProfiles': simliarProfiles,
        'show_similar': show_similar
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
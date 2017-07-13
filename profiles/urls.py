from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(?P<id>[0-9a-f-]+)/$', views.full, name='full'),
]
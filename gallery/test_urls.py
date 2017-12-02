# coding: utf-8

from __future__ import unicode_literals

from django.conf.urls import include, url
from django.contrib import admin

from . import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^private(?P<path>/.+)$', views.serve_private_media),
    url(r'^', include('gallery.urls', namespace='gallery')),
]

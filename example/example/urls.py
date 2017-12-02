# coding: utf-8

from __future__ import unicode_literals

from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^', include('gallery.urls', namespace='gallery')),
]

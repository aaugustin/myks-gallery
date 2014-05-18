# coding: utf-8
# Copyright (c) 2011-2012 Aymeric Augustin. All rights reserved.

from __future__ import unicode_literals

from django.conf.urls import url, include
from django.contrib import admin

from . import views


admin.autodiscover()

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^private(?P<path>/.+)$', views.serve_private_media, name='gallery:album'),
    url(r'^', include('gallery.urls', namespace='gallery', app_name='gallery')),
]

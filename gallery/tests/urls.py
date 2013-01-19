# coding: utf-8
# Copyright (c) 2011-2012 Aymeric Augustin. All rights reserved.

from django.conf.urls import patterns, url, include
from django.contrib import admin

from .. import views


admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^private(?P<path>/.+)$', views.serve_private_media, name='gallery:album'),
    url(r'^', include('gallery.urls', namespace='gallery', app_name='gallery')),
)

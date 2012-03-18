# coding: utf-8
# Copyright (c) 2011-2012 Aymeric Augustin. All rights reserved.

from django.conf.urls import patterns, url

from .. import urls
from .. import views

urlpatterns = urls.urlpatterns

urlpatterns += patterns('',
    url(r'^private(?P<path>/.+)$', views.serve_private_media, name='gallery-album'),
)

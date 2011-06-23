# coding: utf-8
# Copyright (c) 2011 Aymeric Augustin. All rights reserved.

from django.conf.urls.defaults import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'^$', views.GalleryView.as_view(), name='gallery-root'),
    url(r'^(?P<pk>[0-9]+)/$', views.AlbumView.as_view(), name='gallery-album'),
    url(r'^([0-9]+)/(?P<pk>[0-9]+)/$', views.PhotoView.as_view(), name='gallery-photo'),
    url(r'^original/([0-9]+)/$', views.original_photo, name='gallery-photo-original'),
    url(r'^(\w+)/([0-9]+)/$', views.resized_photo, name='gallery-photo-resized'),
)

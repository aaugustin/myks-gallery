# coding: utf-8
# Copyright (c) 2011 Aymeric Augustin. All rights reserved.

from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'^$', views.GalleryView.as_view(), name='gallery-root'),
    url(r'^album/(?P<pk>\d+)/$', views.AlbumView.as_view(), name='gallery-album'),
    url(r'^photo/(?P<pk>\d+)/$', views.PhotoView.as_view(), name='gallery-photo'),
    url(r'^original/(?P<pk>\d+)/$', views.original_photo, name='gallery-photo-original'),
    url(r'^(?P<preset>\w+)/(?P<pk>\d+)/$', views.resized_photo, name='gallery-photo-resized'),
)

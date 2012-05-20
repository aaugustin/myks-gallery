# coding: utf-8
# Copyright (c) 2011-2012 Aymeric Augustin. All rights reserved.

from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns('',
    url(r'^$', views.GalleryIndexView.as_view(), name='gallery-index'),
    url(r'^year/(?P<year>\d{4})/$', views.GalleryYearView.as_view(), name='gallery-year'),
    url(r'^album/(?P<pk>\d+)/$', views.AlbumView.as_view(), name='gallery-album'),
    url(r'^photo/(?P<pk>\d+)/$', views.PhotoView.as_view(), name='gallery-photo'),
    url(r'^original/(?P<pk>\d+)/$', views.original_photo, name='gallery-photo-original'),
    url(r'^(?P<preset>\w+)/(?P<pk>\d+)/$', views.resized_photo, name='gallery-photo-resized'),
)

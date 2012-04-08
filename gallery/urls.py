# coding: utf-8
# Copyright (c) 2011-2012 Aymeric Augustin. All rights reserved.

from django.conf.urls import patterns, url
from django.contrib.auth.decorators import permission_required

from . import views

protect = permission_required('gallery.view')

urlpatterns = patterns('',
    url(r'^$', protect(views.GalleryIndexView.as_view()), name='gallery-index'),
    url(r'^year/(?P<year>\d{4})/$', protect(views.GalleryYearView.as_view()), name='gallery-year'),
    url(r'^album/(?P<pk>\d+)/$', protect(views.AlbumView.as_view()), name='gallery-album'),
    url(r'^photo/(?P<pk>\d+)/$', protect(views.PhotoView.as_view()), name='gallery-photo'),
    url(r'^original/(?P<pk>\d+)/$', protect(views.original_photo), name='gallery-photo-original'),
    url(r'^(?P<preset>\w+)/(?P<pk>\d+)/$', protect(views.resized_photo), name='gallery-photo-resized'),
)

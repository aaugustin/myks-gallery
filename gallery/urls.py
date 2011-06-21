# coding: utf-8
# Copyright (c) 2011 Aymeric Augustin. All rights reserved.

from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('gallery.views',
    url(r'^$', 'show_gallery'),
    url(r'^([0-9]+)/$', 'show_album'),
    url(r'^([0-9]+)/([0-9]+)/$', 'show_photo'),
    url(r'^original/([0-9]+)/$', 'original_photo'),
    url(r'^resized/([0-9]+)/([0-9]+)/([0-9]+)/$', 'resized_photo'),
)

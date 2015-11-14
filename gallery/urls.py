# coding: utf-8

from __future__ import unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.GalleryIndexView.as_view(), name='index'),
    url(r'^year/(?P<year>\d{4})/$', views.GalleryYearView.as_view(), name='year'),
    url(r'^album/(?P<pk>\d+)/$', views.AlbumView.as_view(), name='album'),
    url(r'^export/(?P<pk>\d+)/$', views.export_album, name='album-export'),
    url(r'^photo/(?P<pk>\d+)/$', views.PhotoView.as_view(), name='photo'),
    url(r'^original/(?P<pk>\d+)/$', views.original_photo, name='photo-original'),
    url(r'^(?P<preset>\w+)/(?P<pk>\d+)/$', views.resized_photo, name='photo-resized'),
    url(r'^latest/$', views.latest_album, name='latest'),
]

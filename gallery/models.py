# coding: utf-8
# Copyright (c) 2011-2012 Aymeric Augustin. All rights reserved.

import hashlib
import os

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.db import models

from .imgutil import make_thumbnail


class AccessPolicy(models.Model):
    public = models.BooleanField(verbose_name="is public")
    groups = models.ManyToManyField(Group, blank=True, verbose_name="authorized groups")
    users = models.ManyToManyField(User, blank=True, verbose_name="authorized users")

    class Meta:
        abstract = True


class Album(models.Model):
    category = models.CharField(max_length=100)
    dirpath = models.CharField(max_length=200, verbose_name="directory path")
    date = models.DateField()
    name = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ('-date', 'name', 'dirpath')
        unique_together = ('dirpath', 'category')

    def __unicode__(self):
        return self.dirpath

    @property
    def display_name(self):
        return self.name or self.dirpath.replace(u'/', u' > ')

    @models.permalink
    def get_absolute_url(self):
        return 'gallery-album', [self.pk]


class AlbumAccessPolicy(AccessPolicy):
    album = models.OneToOneField(Album, related_name='access_policy')


class Photo(models.Model):
    album = models.ForeignKey(Album)
    filename = models.CharField(max_length=100, verbose_name="file name")
    date = models.DateTimeField(null=True, blank=True)

    class Meta:
        order_with_respect_to = 'album'
        ordering = ('date', 'filename')
        permissions = (
            ("view", "Can see all photos"),
            ("scan", "Can scan the photos directory"),
        )
        unique_together = ('album', 'filename')

    def __unicode__(self):
        return self.filename

    @property
    def display_name(self):
        return self.date or os.path.splitext(self.filename)[0]

    @models.permalink
    def get_absolute_url(self):
        return 'gallery-photo', [self.pk]

    def abspath(self):
        return os.path.join(settings.PHOTO_ROOT, self.album.dirpath, self.filename)

    def thumbname(self, preset):
        ext = os.path.splitext(self.filename)[1]
        hsh = hashlib.sha1()
        hsh.update(self.album.dirpath.encode('utf-8'))
        hsh.update(self.filename.encode('utf-8'))
        hsh.update(str(settings.PHOTO_RESIZE_PRESETS[preset]))
        return hsh.hexdigest() + ext

    def thumbnail(self, preset):
        thumbpath = os.path.join(settings.PHOTO_CACHE, self.thumbname(preset))
        if not os.path.exists(thumbpath):
            make_thumbnail(self.abspath(), thumbpath, preset)
        return thumbpath


class PhotoAccessPolicy(AccessPolicy):
    photo = models.OneToOneField(Photo, related_name='access_policy')

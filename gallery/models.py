# coding: utf-8
# Copyright (c) 2011 Aymeric Augustin. All rights reserved.

import hashlib
import os

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models

from .imgutil import make_thumbnail

class Album(models.Model):
    dirpath = models.CharField(max_length=200, unique=True,
            verbose_name="directory path")
    date = models.DateField(null=True, blank=True)
    name = models.CharField(max_length=100, blank=True)

    def __unicode__(self):
        return self.name or self.dirpath

    def get_absolute_url(self):
        return reverse('gallery-album', args=[self.pk])


class Photo(models.Model):
    album = models.ForeignKey(Album)
    filename = models.CharField(max_length=100,
        verbose_name="file name")
    date = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('album', 'filename')

    def __unicode__(self):
        return self.filename

    def get_absolute_url(self):
        return reverse('gallery-photo', args=[self.album.pk, self.pk])

    def abspath(self):
        return os.path.join(settings.PHOTO_ROOT, self.album.dirpath, self.filename)

    def thumbname(self, size):
        ext = os.path.splitext(self.filename)[1]
        hsh = hashlib.sha1()
        hsh.update(self.album.dirpath)
        hsh.update(self.filename)
        hsh.update(str(size))
        return hsh.hexdigest() + ext

    def thumbnail(self, preset):
        thumbpath = os.path.join(settings.PHOTO_CACHE, self.thumbname(size))
        if not os.path.exists(thumbpath):
            make_thumbnail(self.abspath(), thumbpath, preset)
        return thumbpath




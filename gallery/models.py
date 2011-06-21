# coding: utf-8
# Copyright (c) 2011 Aymeric Augustin. All rights reserved.

import os

from django.conf import settings
from django.db import models


class Album(models.Model):
    dirpath = models.CharField(max_length=200, unique=True,
            verbose_name="directory path")
    date = models.DateField(null=True, blank=True)
    name = models.CharField(max_length=100, blank=True)

    def __unicode__(self):
        return self.name or self.dirpath

    def get_absolute_url(self):
        raise NotImplementedError


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
        raise NotImplementedError

    @property
    def abspath(self):
        return os.path.join(settings.PHOTO_ROOT, self.album.dirpath, self.filename)

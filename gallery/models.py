# coding: utf-8
# Copyright (c) 2011-2012 Aymeric Augustin. All rights reserved.

import hashlib
import os

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models import Q

from .imgutil import make_thumbnail


class AccessPolicy(models.Model):
    public = models.BooleanField(verbose_name="is public")
    groups = models.ManyToManyField(Group, blank=True, verbose_name="authorized groups")
    users = models.ManyToManyField(User, blank=True, verbose_name="authorized users")

    class Meta:
        abstract = True


class AlbumManager(models.Manager):

    def allowed_for_user(self, user):
        album_conditions = (Q(access_policy__public=True)
                | Q(access_policy__users=user)
                | Q(access_policy__groups__user=user))
        return self.filter(album_conditions)


class Album(models.Model):
    category = models.CharField(max_length=100)
    dirpath = models.CharField(max_length=200, verbose_name="directory path")
    date = models.DateField()
    name = models.CharField(max_length=100, blank=True)

    objects = AlbumManager()

    class Meta:
        ordering = ('-date', 'name', 'dirpath')
        unique_together = ('dirpath', 'category')

    def __unicode__(self):
        return self.dirpath

    @models.permalink
    def get_absolute_url(self):
        return 'gallery-album', [self.pk]

    @property
    def display_name(self):
        return self.name or self.dirpath.replace(u'/', u' > ')

    def is_allowed_for_user(self, user):
        return Album.objects.allowed_for_user(user).filter(pk=self.pk).exists()


class AlbumAccessPolicy(AccessPolicy):
    album = models.OneToOneField(Album, related_name='access_policy')
    inherit = models.BooleanField(blank=True, default=True,
            verbose_name="photos inherit album access policy")


class PhotoManager(models.Manager):

    def allowed_for_user(self, user):
        photo_conditions = (Q(access_policy__public=True)
                | Q(access_policy__users=user)
                | Q(access_policy__groups__user=user))
        inherit = Q(album__access_policy__inherit=True)
        album_conditions = (Q(album__access_policy__public=True)
                | Q(album__access_policy__users=user)
                | Q(album__access_policy__groups__user=user))
        return self.filter(photo_conditions | (inherit & album_conditions))


class Photo(models.Model):
    album = models.ForeignKey(Album)
    filename = models.CharField(max_length=100, verbose_name="file name")
    date = models.DateTimeField(null=True, blank=True)

    objects = PhotoManager()

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

    @models.permalink
    def get_absolute_url(self):
        return 'gallery-photo', [self.pk]

    @property
    def display_name(self):
        return self.date or os.path.splitext(self.filename)[0]

    def get_effective_access_policy(self):
        if self.access_policy:
            return self.access_policy
        elif self.album.access_policy and self.album.access_policy.inherit:
            return self.album.access_policy

    def is_allowed_for_user(self, user):
        return Photo.objects.allowed_for_user(user).filter(pk=self.pk).exists()

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

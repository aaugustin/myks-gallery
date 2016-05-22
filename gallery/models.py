# coding: utf-8

from __future__ import unicode_literals

import hashlib
import os

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.db import models
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from .imgutil import make_thumbnail
from .storages import get_storage


class AccessPolicy(models.Model):
    public = models.BooleanField(verbose_name="is public", default=False)
    groups = models.ManyToManyField(Group, blank=True, verbose_name="authorized groups")
    users = models.ManyToManyField(User, blank=True, verbose_name="authorized users")

    class Meta:
        abstract = True

    def allows(self, user):
        if self.public:
            return True
        if user.is_authenticated():
            if set(self.groups.all()) & set(user.groups.all()):
                return True
            if user in self.users.all():
                return True
        return False


class AlbumManager(models.Manager):

    def allowed_for_user(self, user, include_public=True):
        album_cond = Q()
        if include_public:
            album_cond |= Q(access_policy__public=True)
        if user.is_authenticated():
            album_cond |= Q(access_policy__users=user)
            album_cond |= Q(access_policy__groups__user=user)
        return self.filter(album_cond).distinct()


@python_2_unicode_compatible
class Album(models.Model):
    category = models.CharField(max_length=100)
    dirpath = models.CharField(max_length=200, verbose_name="directory path")
    date = models.DateField()
    name = models.CharField(max_length=100, blank=True)

    objects = AlbumManager()

    class Meta:
        ordering = ('date', 'name', 'dirpath', 'category')
        unique_together = ('dirpath', 'category')
        verbose_name = _("Album")
        verbose_name_plural = _("Albums")

    def __str__(self):
        return self.dirpath

    @models.permalink
    def get_absolute_url(self):
        return 'gallery:album', [self.pk]

    @property
    def display_name(self):
        return self.name or self.dirpath.replace('/', ' > ')

    def get_access_policy(self):
        try:
            return self.access_policy
        except AlbumAccessPolicy.DoesNotExist:
            pass

    def is_allowed_for_user(self, user):
        access_policy = self.get_access_policy()
        return access_policy is not None and access_policy.allows(user)

    def get_next_in_queryset(self, albums):
        albums = albums.filter(
            Q(date__gt=self.date) |
            Q(date=self.date, name__gt=self.name) |
            Q(date=self.date, name=self.name, dirpath__gt=self.dirpath) |
            Q(date=self.date, name=self.name, dirpath=self.dirpath, category__gt=self.category))
        return albums.order_by('date', 'name', 'dirpath', 'category')[:1].get()

    def get_previous_in_queryset(self, albums):
        albums = albums.filter(
            Q(date__lt=self.date) |
            Q(date=self.date, name__lt=self.name) |
            Q(date=self.date, name=self.name, dirpath__lt=self.dirpath) |
            Q(date=self.date, name=self.name, dirpath=self.dirpath, category__lt=self.category))
        return albums.order_by('-date', '-name', '-dirpath', '-category')[:1].get()


@python_2_unicode_compatible
class AlbumAccessPolicy(AccessPolicy):
    album = models.OneToOneField(Album, on_delete=models.CASCADE, related_name='access_policy')
    inherit = models.BooleanField(blank=True, default=True,
                                  verbose_name="photos inherit album access policy")

    class Meta:
        verbose_name = _("Album access policy")
        verbose_name_plural = _("Album access policies")

    def __str__(self):
        return "Access policy for %s" % self.album


class PhotoManager(models.Manager):

    def allowed_for_user(self, user):
        photo_cond = Q(access_policy__public=True)
        inherit = Q(album__access_policy__inherit=True)
        album_cond = Q(album__access_policy__public=True)
        if user.is_authenticated():
            photo_cond |= Q(access_policy__users=user)
            photo_cond |= Q(access_policy__groups__user=user)
            album_cond |= Q(album__access_policy__users=user)
            album_cond |= Q(album__access_policy__groups__user=user)
        return self.filter(photo_cond | (inherit & album_cond)).distinct()


@python_2_unicode_compatible
class Photo(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    filename = models.CharField(max_length=100, verbose_name="file name")
    date = models.DateTimeField(null=True, blank=True)

    objects = PhotoManager()

    class Meta:
        ordering = ('date', 'filename')
        permissions = (
            ("view", "Can see all photos"),
            ("scan", "Can scan the photos directory"),
        )
        unique_together = ('album', 'filename')
        verbose_name = _("Photo")
        verbose_name_plural = _("Photos")

    def __str__(self):
        return self.filename

    @models.permalink
    def get_absolute_url(self):
        return 'gallery:photo', [self.pk]

    @property
    def display_name(self):
        return self.date or os.path.splitext(self.filename)[0]

    def get_effective_access_policy(self):
        try:
            return self.access_policy
        except PhotoAccessPolicy.DoesNotExist:
            pass
        try:
            album_access_policy = self.album.access_policy
        except AlbumAccessPolicy.DoesNotExist:
            pass
        else:
            if album_access_policy.inherit:
                return album_access_policy

    def is_allowed_for_user(self, user):
        access_policy = self.get_effective_access_policy()
        return access_policy is not None and access_policy.allows(user)

    # In the next two functions, images whose date is None may come
    # first or last, depending on the database.
    # These expressions are optimized for clarity, not concision.

    def get_next_in_queryset(self, photos):
        if self.date is None:
            photos = photos.filter(
                Q(date__isnull=False) |
                Q(date__isnull=True, filename__gt=self.filename))
        else:
            photos = photos.filter(
                Q(date__gt=self.date) |
                Q(date=self.date, filename__gt=self.filename))
        return photos.order_by('date', 'filename')[:1].get()

    def get_previous_in_queryset(self, photos):
        if self.date is None:
            photos = photos.filter(
                date__isnull=True, filename__lt=self.filename)
        else:
            photos = photos.filter(
                Q(date__isnull=True) |
                Q(date__lt=self.date) |
                Q(date=self.date, filename__gt=self.filename))
        return photos.order_by('-date', '-filename')[:1].get()

    def image_name(self):
        return os.path.join(self.album.dirpath, self.filename)

    def thumb_name(self, preset):
        prefix = self.album.date.strftime('%y%m')
        hsh = hashlib.md5()
        hsh.update(str(settings.SECRET_KEY).encode())
        hsh.update(str(self.album.pk).encode())
        hsh.update(str(self.pk).encode())
        hsh.update(str(settings.GALLERY_RESIZE_PRESETS[preset]).encode())
        ext = os.path.splitext(self.filename)[1].lower()
        return os.path.join(prefix, hsh.hexdigest() + ext)

    def thumbnail(self, preset):
        image_name = self.image_name()
        thumb_name = self.thumb_name(preset)
        photo_storage = get_storage('photo')
        cache_storage = get_storage('cache')
        if not cache_storage.exists(thumb_name):
            make_thumbnail(image_name, thumb_name, preset,
                           photo_storage, cache_storage)
        return thumb_name


@python_2_unicode_compatible
class PhotoAccessPolicy(AccessPolicy):
    photo = models.OneToOneField(Photo, on_delete=models.CASCADE, related_name='access_policy')

    class Meta:
        verbose_name = _("Photo access policy")
        verbose_name_plural = _("Photo access policies")

    def __str__(self):
        return "Access policy for %s" % self.photo

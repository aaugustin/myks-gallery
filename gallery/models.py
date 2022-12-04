import os

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .resizers import get_resize


class AccessPolicy(models.Model):
    public = models.BooleanField(verbose_name="is public", default=False)
    groups = models.ManyToManyField(Group, blank=True, verbose_name="authorized groups")
    users = models.ManyToManyField(User, blank=True, verbose_name="authorized users")

    class Meta:
        abstract = True

    def allows(self, user):
        if self.public:
            return True
        if user.is_authenticated:
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
        if user.is_authenticated:
            album_cond |= Q(access_policy__users=user)
            album_cond |= Q(access_policy__groups__user=user)
        return self.filter(album_cond).distinct()


class Album(models.Model):
    category = models.CharField(max_length=100)
    dirpath = models.CharField(max_length=200, verbose_name="directory path")
    date = models.DateField()
    name = models.CharField(max_length=100, blank=True)

    objects = AlbumManager()

    class Meta:
        ordering = ("date", "name", "dirpath", "category")
        unique_together = ("dirpath", "category")
        verbose_name = _("album")
        verbose_name_plural = _("albums")

    def __str__(self):
        return self.dirpath

    def get_absolute_url(self):
        return reverse("gallery:album", args=[self.pk])

    @property
    def display_name(self):
        return self.name or self.dirpath.replace("/", " > ")

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
            Q(date__gt=self.date)
            | Q(date=self.date, name__gt=self.name)
            | Q(date=self.date, name=self.name, dirpath__gt=self.dirpath)
            | Q(
                date=self.date,
                name=self.name,
                dirpath=self.dirpath,
                category__gt=self.category,
            )
        )
        return albums.order_by("date", "name", "dirpath", "category")[:1].get()

    def get_previous_in_queryset(self, albums):
        albums = albums.filter(
            Q(date__lt=self.date)
            | Q(date=self.date, name__lt=self.name)
            | Q(date=self.date, name=self.name, dirpath__lt=self.dirpath)
            | Q(
                date=self.date,
                name=self.name,
                dirpath=self.dirpath,
                category__lt=self.category,
            )
        )
        return albums.order_by("-date", "-name", "-dirpath", "-category")[:1].get()


class AlbumAccessPolicy(AccessPolicy):
    album = models.OneToOneField(
        Album, on_delete=models.CASCADE, related_name="access_policy"
    )
    inherit = models.BooleanField(
        blank=True, default=True, verbose_name="photos inherit album access policy"
    )

    class Meta:
        verbose_name = _("album access policy")
        verbose_name_plural = _("album access policies")

    def __str__(self):
        return f"Access policy for {self.album}"


class PhotoManager(models.Manager):
    def allowed_for_user(self, user):
        inherit = Q(access_policy__isnull=True, album__access_policy__inherit=True)
        photo_cond = Q(access_policy__public=True)
        album_cond = Q(album__access_policy__public=True)
        if user.is_authenticated:
            photo_cond |= Q(access_policy__users=user)
            photo_cond |= Q(access_policy__groups__user=user)
            album_cond |= Q(album__access_policy__users=user)
            album_cond |= Q(album__access_policy__groups__user=user)
        return self.filter(photo_cond | (inherit & album_cond)).distinct()


class Photo(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    filename = models.CharField(max_length=100, verbose_name="file name")
    date = models.DateTimeField(null=True, blank=True)

    objects = PhotoManager()

    class Meta:
        ordering = ("date", "filename")
        permissions = (
            ("view", "Can see all photos"),
            ("scan", "Can scan the photos directory"),
        )
        unique_together = ("album", "filename")
        verbose_name = _("photo")
        verbose_name_plural = _("photos")

    def __str__(self):
        return self.filename

    def get_absolute_url(self):
        return reverse("gallery:photo", args=[self.pk])

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
                Q(date__isnull=False) | Q(date__isnull=True, filename__gt=self.filename)
            )
        else:
            photos = photos.filter(
                Q(date__gt=self.date) | Q(date=self.date, filename__gt=self.filename)
            )
        return photos.order_by("date", "filename")[:1].get()

    def get_previous_in_queryset(self, photos):
        if self.date is None:
            photos = photos.filter(date__isnull=True, filename__lt=self.filename)
        else:
            photos = photos.filter(
                Q(date__isnull=True)
                | Q(date__lt=self.date)
                | Q(date=self.date, filename__gt=self.filename)
            )
        return photos.order_by("-date", "-filename")[:1].get()

    @property
    def image_name(self):
        return os.path.join(self.album.dirpath, self.filename)

    def resized_url(self, preset):
        resize = get_resize()
        width, height, crop = settings.GALLERY_RESIZE_PRESETS[preset]
        return resize(self, width, height, crop)


class PhotoAccessPolicy(AccessPolicy):
    photo = models.OneToOneField(
        Photo, on_delete=models.CASCADE, related_name="access_policy"
    )

    class Meta:
        verbose_name = _("photo access policy")
        verbose_name_plural = _("photo access policies")

    def __str__(self):
        return f"Access policy for {self.photo}"

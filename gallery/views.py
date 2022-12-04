import hashlib
import os
import random
import tempfile
import zipfile

from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.functional import cached_property
from django.views.generic import ArchiveIndexView, DetailView, YearArchiveView

from .models import Album, Photo
from .storages import get_storage


class GalleryCommonMixin:
    allow_future = True

    @cached_property
    def can_view_all(self):
        """
        Can the user view all photos, regardless of access policies?

        """
        return self.request.user.has_perm("gallery.view")

    @cached_property
    def show_public(self):
        """
        Should public albums be displayed, or only private ones?

        When the same gallery contains both public and private albums,
        authenticated users only see private albums by default, unless
        they have access to all photos.

        """
        session = self.request.session
        if self.request.user.is_authenticated and not self.can_view_all:
            if "show_public" in self.request.GET:
                session["show_public"] = True
            elif "hide_public" in self.request.GET:
                session["show_public"] = False
            return session.get("show_public", False)
        else:
            return True


class AlbumListMixin:
    """
    Perform access control and database optimization for albums.

    """

    model = Album
    date_field = "date"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["show_public"] = self.show_public
        return context

    def get_queryset(self):
        if self.can_view_all:
            qs = Album.objects.all()
            qs = qs.prefetch_related("photo_set")
        else:
            qs = Album.objects.allowed_for_user(self.request.user, self.show_public)
            qs = qs.prefetch_related("access_policy__groups")
            qs = qs.prefetch_related("access_policy__users")
            qs = qs.prefetch_related("photo_set__access_policy__groups")
            qs = qs.prefetch_related("photo_set__access_policy__users")
        return qs.order_by("-date", "-name")


class AlbumListWithPreviewMixin(AlbumListMixin):
    """
    Compute preview lists for albums.

    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if not self.can_view_all and user.is_authenticated:
            # Avoid repeated queries - this is specific to django.contrib.auth
            user = User.objects.prefetch_related("groups").get(pk=user.pk)
        for album in context["object_list"]:
            if self.can_view_all:
                photos = list(album.photo_set.all())
            else:
                photos = [
                    photo
                    for photo in album.photo_set.all()
                    if photo.is_allowed_for_user(user)
                ]
            album.photos_count = len(photos)
            preview_count = getattr(settings, "GALLERY_PREVIEW_COUNT", 5)
            if len(photos) > preview_count:
                selection = sorted(
                    random.sample(range(album.photos_count), preview_count)
                )
                album.preview = [photos[index] for index in selection]
            else:
                album.preview = list(photos)
        context["title"] = getattr(settings, "GALLERY_TITLE", "Gallery")
        return context


class GalleryIndexView(GalleryCommonMixin, AlbumListWithPreviewMixin, ArchiveIndexView):
    allow_empty = True
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        query = self.request.GET.get("q", "")
        if query:
            qs = qs.filter(name__contains=query)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "")
        if query:
            context["q"] = query
        return context


class GalleryYearView(GalleryCommonMixin, AlbumListWithPreviewMixin, YearArchiveView):
    make_object_list = True
    paginate_by = 20


class AlbumView(GalleryCommonMixin, AlbumListMixin, DetailView):
    model = Album
    context_object_name = "album"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.can_view_all:
            context["photos"] = self.object.photo_set.all()
        else:
            context["photos"] = self.object.photo_set.allowed_for_user(
                self.request.user
            )
        if self.can_view_all:
            qs = Album.objects.all()
        else:
            qs = Album.objects.allowed_for_user(self.request.user, self.show_public)
        try:
            context["previous_album"] = self.object.get_previous_in_queryset(qs)
        except Album.DoesNotExist:
            pass
        try:
            context["next_album"] = self.object.get_next_in_queryset(qs)
        except Album.DoesNotExist:
            pass
        return context


class PhotoView(GalleryCommonMixin, DetailView):
    model = Photo
    context_object_name = "photo"

    def get_queryset(self):
        if self.can_view_all:
            qs = Photo.objects.all()
        else:
            qs = Photo.objects.allowed_for_user(self.request.user)
        return qs.select_related("album")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.can_view_all:
            qs = self.object.album.photo_set.all()
        else:
            qs = self.object.album.photo_set.allowed_for_user(self.request.user)
        try:
            context["previous_photo"] = self.object.get_previous_in_queryset(qs)
        except Photo.DoesNotExist:
            pass
        try:
            context["next_photo"] = self.object.get_next_in_queryset(qs)
        except Photo.DoesNotExist:
            pass
        return context


def export_album(request, pk):
    """
    Serve a zip archive containing an entire album.

    """
    album = get_object_or_404(Album, pk=pk)
    if request.user.has_perm("gallery.view"):
        photos = album.photo_set.all()
    else:
        photos = album.photo_set.allowed_for_user(request.user)

    zip_storage = get_storage("cache")
    image_storage = get_storage("photo")

    hsh = hashlib.md5()
    hsh.update(str(settings.SECRET_KEY).encode())
    hsh.update(str(pk).encode())
    for photo in photos:
        hsh.update(str(photo.pk).encode())
    zip_name = os.path.join("export", hsh.hexdigest() + ".zip")

    if not zip_storage.exists(zip_name):
        # Create the archive in a temporary file to avoid holding it in memory
        with tempfile.TemporaryFile(suffix=".zip") as temp_zip:
            with zipfile.ZipFile(temp_zip, "w") as archive:
                for photo in photos:
                    data = image_storage.open(photo.image_name).read()
                    archive.writestr(photo.filename, data)
            temp_zip.seek(0)
            zip_storage.save(zip_name, temp_zip)

    zip_url = zip_storage.url(zip_name)
    return HttpResponseRedirect(zip_url)


def _get_photo_if_allowed(request, pk):
    qs = Photo.objects
    if not request.user.has_perm("gallery.view"):
        qs = qs.allowed_for_user(request.user)
    qs = qs.select_related("album")
    return get_object_or_404(qs, pk=pk)


def resized_photo(request, preset, pk):
    """Serve a resized photo."""
    photo = _get_photo_if_allowed(request, int(pk))
    return HttpResponseRedirect(photo.resized_url(preset))


def original_photo(request, pk):
    """Serve an original photo."""
    photo = _get_photo_if_allowed(request, int(pk))
    return HttpResponseRedirect(get_storage("photo").url(photo.image_name))


def latest_album(request):
    if request.user.has_perm("gallery.view"):
        albums = Album.objects.all()
    else:
        include_public = request.session.get(
            "show_public", not request.user.is_authenticated
        )
        albums = Album.objects.allowed_for_user(request.user, include_public)
    albums = albums.order_by("-date")[:1]
    if albums:
        pk = albums[0].pk
        return HttpResponseRedirect(reverse("gallery:album", args=[pk]))
    else:
        return HttpResponseRedirect(reverse("gallery:index"))

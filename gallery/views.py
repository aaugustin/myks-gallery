# coding: utf-8
# Copyright (c) 2011-2012 Aymeric Augustin. All rights reserved.

from __future__ import unicode_literals

import glob
import hashlib
import mimetypes
import os
import random
import re
import stat
import sys
import time
import unicodedata
import zipfile

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import (Http404, HttpResponse, HttpResponseNotModified,
    HttpResponseRedirect, StreamingHttpResponse)
from django.shortcuts import get_object_or_404
from django.utils.http import http_date
from django.utils import six
from django.views.generic import ArchiveIndexView, DetailView, YearArchiveView
from django.views.static import was_modified_since

from .models import Album, Photo


class GalleryCommonMixin(object):
    """Provide can_view_all() and show_public() utility methods."""
    allow_future = True

    def can_view_all(self):
        if not hasattr(self, '_can_view_all'):
            self._can_view_all = self.request.user.has_perm('gallery.view')
        return self._can_view_all

    def show_public(self):
        session = self.request.session
        if not hasattr(self, '_show_public'):
            if self.request.user.is_authenticated() and not self.can_view_all():
                if 'show_public' in self.request.GET:
                    self._show_public = session['show_public'] = True
                elif 'hide_public' in self.request.GET:
                    self._show_public = session['show_public'] = False
                else:
                    self._show_public = session.setdefault('show_public', False)
            else:
                self._show_public = True
        return self._show_public


class AlbumListMixin(object):
    """Perform access control and database optimization for albums."""
    model = Album
    date_field = 'date'

    def get_context_data(self, **kwargs):
        context = super(AlbumListMixin, self).get_context_data(**kwargs)
        context['show_public'] = self.show_public()
        return context

    def get_queryset(self):
        if self.can_view_all():
            qs = Album.objects.all()
            qs = qs.prefetch_related('photo_set')
        else:
            qs = Album.objects.allowed_for_user(self.request.user, self.show_public())
            qs = qs.prefetch_related('access_policy__groups')
            qs = qs.prefetch_related('access_policy__users')
            qs = qs.prefetch_related('photo_set__access_policy__groups')
            qs = qs.prefetch_related('photo_set__access_policy__users')
        return qs


class AlbumListWithPreviewMixin(AlbumListMixin):
    """Compute preview lists for albums."""

    def get_context_data(self, **kwargs):
        context = super(AlbumListWithPreviewMixin, self).get_context_data(**kwargs)
        user = self.request.user
        if not self.can_view_all() and user.is_authenticated():
            # Avoid repeated queries - this is specific to django.contrib.auth
            user = User.objects.prefetch_related('groups').get(pk=user.pk)
        for album in context['object_list']:
            if self.can_view_all():
                photos = list(album.photo_set.all())
            else:
                photos = [photo for photo in album.photo_set.all()
                                if photo.is_allowed_for_user(user)]
            album.photos_count = len(photos)
            album.preview = random.sample(photos, min(album.photos_count, 5))
        context['title'] = getattr(settings, 'GALLERY_TITLE', "Gallery")
        return context


class GalleryIndexView(GalleryCommonMixin, AlbumListWithPreviewMixin, ArchiveIndexView):
    allow_empty = True
    paginate_by = 10

    def get_queryset(self):
        qs = super(GalleryIndexView, self).get_queryset()
        query = self.request.GET.get('q', '')
        if query:
            qs = qs.filter(name__contains=query)
        return qs

    def get_context_data(self, **kwargs):
        context = super(GalleryIndexView, self).get_context_data(**kwargs)
        query = self.request.GET.get('q', '')
        if query:
            context['q'] = query
        return context


class GalleryYearView(GalleryCommonMixin, AlbumListWithPreviewMixin, YearArchiveView):
    make_object_list = True


class AlbumView(GalleryCommonMixin, AlbumListMixin, DetailView):
    model = Album
    context_object_name = 'album'

    def get_context_data(self, **kwargs):
        context = super(AlbumView, self).get_context_data(**kwargs)
        if self.can_view_all():
            context['photos'] = self.object.photo_set.all()
        else:
            context['photos'] = self.object.photo_set.allowed_for_user(self.request.user)
        if self.can_view_all():
            qs = Album.objects.all()
        else:
            qs = Album.objects.allowed_for_user(self.request.user, self.show_public())
        try:
            context['previous_album'] = self.object.get_previous_in_queryset(qs)
        except Album.DoesNotExist:
            pass
        try:
            context['next_album'] = self.object.get_next_in_queryset(qs)
        except Album.DoesNotExist:
            pass
        return context


class PhotoView(GalleryCommonMixin, DetailView):
    model = Photo
    context_object_name = 'photo'

    def get_queryset(self):
        if self.can_view_all():
            qs = Photo.objects.all()
        else:
            qs = Photo.objects.allowed_for_user(self.request.user)
        return qs.select_related('album')

    def get_context_data(self, **kwargs):
        context = super(PhotoView, self).get_context_data(**kwargs)
        if self.can_view_all():
            qs = self.object.album.photo_set.all()
        else:
            qs = self.object.album.photo_set.allowed_for_user(self.request.user)
        try:
            context['previous_photo'] = self.object.get_previous_in_queryset(qs)
        except Photo.DoesNotExist:
            pass
        try:
            context['next_photo'] = self.object.get_next_in_queryset(qs)
        except Photo.DoesNotExist:
            pass
        return context


def export_album(request, pk):
    """Serve a zip archive containing an entire album."""
    album = get_object_or_404(Album, pk=pk)
    if request.user.has_perm('gallery.view'):
        photos = album.photo_set.all()
    else:
        photos = album.photo_set.allowed_for_user(request.user)

    hsh = hashlib.sha1()
    for photo in photos:
        hsh.update(photo.filename.encode('utf-8'))
    zip_name = hsh.hexdigest() + '.zip'
    zip_path = os.path.join(settings.GALLERY_CACHE_DIR, 'export', zip_name)

    if not os.path.exists(zip_path):

        zip_dir = os.path.dirname(zip_path)
        if not os.path.isdir(zip_dir):
            os.makedirs(zip_dir)

        archive_expiry = getattr(settings, 'GALLERY_ARCHIVE_EXPIRY', 60)
        cutoff = time.time() - archive_expiry * 86400
        for zip_file in glob.glob(os.path.join(zip_dir, '*.zip')):
            if os.path.getmtime(zip_file) < cutoff:
                os.unlink(zip_file)

        with zipfile.ZipFile(zip_path, 'w') as archive:
            for photo in photos:
                archive.write(photo.abspath(), photo.filename)

    response = serve_private_media(request, zip_path)

    ascii_filename = '%s_%s.zip' % (str(album.date), sanitize(album.name))
    response['Content-Disposition'] = 'attachement; filename=%s;' % ascii_filename
    return response


def _get_photo_if_allowed(request, pk):
    qs = Photo.objects
    if not request.user.has_perm('gallery.view'):
        qs = qs.allowed_for_user(request.user)
    qs = qs.select_related('album')
    return get_object_or_404(qs, pk=pk)


def resized_photo(request, preset, pk):
    """Serve a resized photo."""
    photo = _get_photo_if_allowed(request, int(pk))
    path = photo.thumbnail(preset)
    response = serve_private_media(request, path)

    root, ext = os.path.splitext(sanitize(photo.filename))
    width, height, _ = settings.GALLERY_RESIZE_PRESETS[preset]
    ascii_filename = '%s_%sx%s%s' % (root, width, height, ext)
    response['Content-Disposition'] = 'inline; filename=%s;' % ascii_filename
    return response


def original_photo(request, pk):
    """Serve an original photo."""
    photo = _get_photo_if_allowed(request, int(pk))
    path = photo.abspath()
    response = serve_private_media(request, path)

    ascii_filename = sanitize(photo.filename)
    response['Content-Disposition'] = 'inline; filename=%s;' % ascii_filename
    return response


def serve_private_media(request, path):
    """Serve a private media file with the webserver's "sendfile" if possible.

    Here's an example of how to use this function. The 'Document' model tracks
    files. It provides a 'get_file_path' method returning the absolute path to
    the actual file. The following view serves file only to users having the
    'can_download' permission::

        @permission_required('documents.can_download')
        def download_document(request, document_id):
            path = Document.objects.get(pk=document_id).get_file_path()
            return serve_private_media(request, path)

    If ``DEBUG`` is ``False`` and ``settings.GALLERY_SENDFILE_HEADER`` is set,
    this function sets a header and doesn't send the actual contents of the
    file. Use ``'X-Accel-Redirect'`` for nginx and ``'X-SendFile'`` for Apache
    with mod_xsendfile. Otherwise, this function behaves like Django's static
    serve view.

    ``path`` must be an absolute path. Depending on your webserver's
    configuration, you might want a full path or a relative path in the
    header's value. ``settings.GALLERY_SENDFILE_ROOT`` will be stripped from
    the beginning of the path to create the header's value.
    """

    if not os.path.exists(path):
        # Don't reveal the file name on the filesystem.
        raise Http404("Requested file doesn't exist.")

    # begin copy-paste from django.views.static.serve
    statobj = os.stat(path)
    content_type, encoding = mimetypes.guess_type(path)
    content_type = content_type or 'application/octet-stream'
    if not was_modified_since(request.META.get('HTTP_IF_MODIFIED_SINCE'),
                              statobj.st_mtime, statobj.st_size):   # pragma: no cover
        return HttpResponseNotModified()
    # pause copy-paste from django.views.static.serve

    sendfile_header = getattr(settings, 'GALLERY_SENDFILE_HEADER', '')
    sendfile_root = getattr(settings, 'GALLERY_SENDFILE_ROOT', '')

    if settings.DEBUG or not sendfile_header:
        response = StreamingHttpResponse(open(path, 'rb'), content_type=content_type)
    else:
        response = HttpResponse('', content_type=content_type)
        if sendfile_root:
            if not path.startswith(sendfile_root):
                raise ValueError("Requested file isn't under GALLERY_SENDFILE_ROOT.")
            path = path[len(sendfile_root):]
        response[sendfile_header] = path.encode(sys.getfilesystemencoding())

    # resume copy-paste from django.views.static.serve
    response["Last-Modified"] = http_date(statobj.st_mtime)
    if stat.S_ISREG(statobj.st_mode):                       # pragma: no cover
        response["Content-Length"] = statobj.st_size
    if encoding:                                            # pragma: no cover
        response["Content-Encoding"] = encoding
    # end copy-paste from django.views.static.serve

    return response


_sanitize_re = re.compile(r'[^0-9A-Za-z_.-]')

def sanitize(value):
    value = unicodedata.normalize('NFKD', six.text_type(value))
    value = value.encode('ascii', 'ignore').decode('ascii')
    value = _sanitize_re.sub('', value.replace(' ', '_'))
    return value


def latest_album(request):
    if request.user.has_perm('gallery.view'):
        albums = Album.objects.all()
    else:
        include_public = request.session.get('show_public',
                not request.user.is_authenticated())
        albums = Album.objects.allowed_for_user(request.user, include_public)
    albums = albums.order_by('-date')[:1]
    if albums:
        pk = albums[0].pk
        return HttpResponseRedirect(reverse('gallery:album', args=[pk]))
    else:
        return HttpResponseRedirect(reverse('gallery:index'))

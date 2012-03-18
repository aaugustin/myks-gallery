# coding: utf-8
# Copyright (c) 2011 Aymeric Augustin. All rights reserved.

import mimetypes
import os
import stat

from django.conf import settings
from django.http import HttpResponse, HttpResponseNotModified, Http404
from django.utils.http import http_date
from django.views.generic import DetailView, ListView
from django.views.static import was_modified_since

from .models import Album, Photo


class GalleryTitleMixin(object):
    def get_context_data(self, **kwargs):
        context = super(GalleryTitleMixin, self).get_context_data(**kwargs)
        context['title'] = getattr(settings, 'PHOTO_TITLE', u"Gallery")
        return context


class GalleryView(GalleryTitleMixin, ListView):
    model = Album
    context_object_name = 'album_list'


class AlbumView(GalleryTitleMixin, DetailView):
    model = Album
    context_object_name = 'album'


class PhotoView(DetailView):
    model = Photo
    context_object_name = 'photo'


def resized_photo(request, preset, photo_id):
    photo = Photo.objects.select_related().get(pk=int(photo_id))
    path = photo.thumbnail(preset)
    prefix = settings.PHOTO_SERVE_CACHE_PREFIX
    root, ext = os.path.splitext(photo.filename.encode('ascii', 'replace'))
    width, height, _ = settings.PHOTO_RESIZE_PRESETS[preset]
    ascii_filename = '%s_%sx%s%s' % (root, width, height, ext)
    headers = {
        'Content-Disposition': 'inline; filename=%s;' % ascii_filename,
    }
    return serve_private_media(request, path, prefix, headers=headers)


def original_photo(request, photo_id):
    photo = Photo.objects.select_related().get(pk=int(photo_id))
    path = photo.abspath()
    prefix = settings.PHOTO_SERVE_PREFIX
    ascii_filename = photo.filename.encode('ascii', 'replace')
    headers = {
        'Content-Disposition': 'attachement; filename=%s;' % ascii_filename,
    }
    return serve_private_media(request, path, prefix, headers=headers)


def serve_private_media(request, path, prefix, headers=None):
    """Serve a private media file.

    Here's an example of how to use this function. We want to serve the file
    stored in the 'file' attribute of a 'Document' model only to users who
    have the 'can_download' permission::

        @permission_required('documents.can_download')
        def download_document(request, document_id):
            path = Document.objects.get(pk=document_id).file.path
            return serve_private_media(request, path)

    If ``DEBUG`` is ``True``, this function will behave like Django's static
    serve view. If ``DEBUG`` is ``False``, it will set a header and won't send
    the actual contents of the file.

    The name of the header is defined by ``settings.MEDIA_HEADER``. Use
    ``X-Accel-Redirect`` for nginx and ``X-SendFile`` for apache.

    path must be an absolute path. Depending on your webserver's configuration,
    the header should contain either a relative path or full path. Therefore,
    prefix will be stripped from the beginning of path to create the header's
    value. prefix should be ``settings.PHOTO_ROOT.rstrip('/')`` for nginx and
    ``''`` for apache.
    """
    if not os.path.exists(path):
        # Don't reveal the file name on the filesystem.
        raise Http404("Requested file does not exist.")

    # begin copy-paste from django.views.static.serve
    statobj = os.stat(path)
    mimetype, encoding = mimetypes.guess_type(path)
    mimetype = mimetype or 'application/octet-stream'
    if not was_modified_since(request.META.get('HTTP_IF_MODIFIED_SINCE'),
                              statobj.st_mtime, statobj.st_size):
        return HttpResponseNotModified(mimetype=mimetype)
    # pause copy-paste from django.views.static.serve

    if settings.DEBUG:
        with open(path, 'rb') as f:
            response = HttpResponse(f.read(), mimetype=mimetype)
    else:
        response = HttpResponse('', mimetype=mimetype)
        assert path.startswith(prefix)
        response[settings.MEDIA_HEADER] = path[len(prefix):]

    # resume copy-paste from django.views.static.serve
    response["Last-Modified"] = http_date(statobj.st_mtime)
    if stat.S_ISREG(statobj.st_mode):
        response["Content-Length"] = statobj.st_size
    if encoding:
        response["Content-Encoding"] = encoding
    # end copy-paste from django.views.static.serve

    if headers:
        for k, v in headers.iteritems():
            response[k] = v

    return response

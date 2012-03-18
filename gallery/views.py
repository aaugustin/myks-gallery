# coding: utf-8
# Copyright (c) 2011-2012 Aymeric Augustin. All rights reserved.

import mimetypes
import os
import stat
import unicodedata

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


def resized_photo(request, preset, pk):
    photo = Photo.objects.select_related().get(pk=int(pk))
    path = photo.thumbnail(preset)
    response = serve_private_media(request, path)

    root, ext = os.path.splitext(asciify(photo.filename))
    width, height, _ = settings.PHOTO_RESIZE_PRESETS[preset]
    ascii_filename = '%s_%sx%s%s' % (root, width, height, ext)
    response['Content-Disposition'] = 'inline; filename=%s;' % ascii_filename
    return response


def original_photo(request, pk):
    photo = Photo.objects.select_related().get(pk=int(pk))
    path = photo.abspath()
    response = serve_private_media(request, path)

    ascii_filename = asciify(photo.filename)
    response['Content-Disposition'] = 'inline; filename=%s;' % ascii_filename
    return response


def serve_private_media(request, path):
    """Serve a private media file.

    Here's an example of how to use this function. We want to serve the file
    stored in the 'file' attribute of a 'Document' model only to users who
    have the 'can_download' permission::

        @permission_required('documents.can_download')
        def download_document(request, document_id):
            path = Document.objects.get(pk=document_id).file.path
            return serve_private_media(request, path)

    If ``DEBUG`` is ``True``, this function behaves like Django's static serve
    view. If ``DEBUG`` is ``False``, it sets a header and doesn't send the
    actual contents of the file.

    The name of the header is defined by ``settings.SENDFILE_HEADER``. Use
    ``'X-Accel-Redirect'`` for nginx and ``'X-SendFile'`` for Apache.

    ``path`` must be an absolute path. Depending on your webserver's
    configuration, the header should contain either a relative path or full
    path. Therefore, ``settings.SENDFILE_ROOT`` will be stripped from the
    beginning of the path to create the header's value. It must be the root of
    the internal location under nginx. It may be XSendFilePath or empty for
    Apache.
    """
    if not os.path.exists(path):
        # Don't reveal the file name on the filesystem.
        raise Http404("Requested file doesn't exist.")

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
        if settings.SENDFILE_ROOT:
            if not path.startswith(settings.SENDFILE_ROOT):
                raise ValueError("Requested file isn't under SENDFILE_ROOT.")
            path = path[len(settings.SENDFILE_ROOT):]
        response[settings.SENDFILE_HEADER] = path

    # resume copy-paste from django.views.static.serve
    response["Last-Modified"] = http_date(statobj.st_mtime)
    if stat.S_ISREG(statobj.st_mode):
        response["Content-Length"] = statobj.st_size
    if encoding:
        response["Content-Encoding"] = encoding
    # end copy-paste from django.views.static.serve

    return response


def asciify(value):
    return unicodedata.normalize('NFKD', unicode(value)).encode('ascii', 'ignore')

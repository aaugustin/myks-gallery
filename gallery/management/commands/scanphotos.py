# coding: utf-8
# Copyright (c) 2011-2012 Aymeric Augustin. All rights reserved.

# If you have non-ascii characters in filenames, you probably need:
# export PYTHONIOENCODING=utf-8

import collections
import datetime
import os
import re
import sys
import time

from django.conf import settings
from django.core.management import base
from django.db import transaction
from django.utils.timezone import get_default_timezone

from ...models import Album, Photo


class Command(base.NoArgsCommand):
    help = 'Scan PHOTO_ROOT and update database.'

    @transaction.commit_on_success
    def handle_noargs(self, **options):
        verbosity = int(options.get('verbosity', 1))
        if verbosity >= 1:
            t = time.time()
            print "Scanning %s" % settings.PHOTO_ROOT
        new_albums = scan_photo_root(verbosity)
        synchronize_albums(new_albums, verbosity)
        synchronize_photos(new_albums, verbosity)
        if verbosity >= 1:
            dt = time.time() - t
            print "Done (%.02fs)" % dt


ignores = [re.compile(pat) for pat in settings.PHOTO_IGNORES]

def is_ignored(path):
    return any(pat.match(path) for pat in ignores)


patterns = [(cat, re.compile(pat)) for cat, pat in settings.PHOTO_PATTERNS]

def is_matched(path):
    for category, pattern in patterns:
        match = pattern.match(path)
        if match:
            return category, match.groupdict()


fs_encoding = sys.getfilesystemencoding()

def iter_photo_root(verbosity=0):
    """Yield relative path, category and regex captures for each photo."""
    for dirpath, _, filenames in os.walk(settings.PHOTO_ROOT):
        dirpath = dirpath.decode(fs_encoding)
        for filename in filenames:
            filename = filename.decode(fs_encoding)
            filepath = os.path.join(dirpath, filename)
            relpath = os.path.relpath(filepath, settings.PHOTO_ROOT)
            if is_ignored(relpath):
                if verbosity >= 3:
                    print "-", relpath
                continue
            result = is_matched(relpath)
            if result is not None:
                if verbosity >= 3:
                    print ">", relpath
                category, captures = result
                yield relpath, category, captures
            else:
                if verbosity >= 2:
                    print "?", relpath


def get_album_info(captures, verbosity):
    """Return the date and name of an album.

    `captures` are elements extracted from the file name of a random photo
    in the album.
    """
    date = None
    try:
        kwargs = dict((k, int(captures['a_' + k]))
                for k in ('year', 'month', 'day'))
        date = datetime.date(**kwargs)
    except KeyError:
        pass
    except ValueError, e:
        if verbosity >= 1:
            print e, kwargs
    name = ' '.join(v for k, v in sorted(captures.iteritems())
                    if k.startswith('a_name') and v is not None)
    name = name.replace(u'/', u' > ')
    return date, name


tz = get_default_timezone()

def get_photo_info(captures, verbosity):
    """Return the datetime of a photo.

    `captures` are elements extracted from the file name of the photo.
    """
    date = None
    try:
        kwargs = dict((k, int(captures['p_' + k]))
                for k in ('year', 'month', 'day', 'hour', 'minute', 'second'))
        date = datetime.datetime(tzinfo=tz, **kwargs)
    except KeyError:
        pass
    except ValueError, e:
        if verbosity >= 1:
            print e, kwargs
    return date


def scan_photo_root(verbosity=0):
    """Return a dictionary of albums, keyed by dirpath.

    Each album is a dictionary of photos, keyed by filename.

    The result can be passed to synchronize_albums and synchronize_photos.
    """
    albums = collections.defaultdict(lambda: {})
    for path, category, captures in iter_photo_root(verbosity):
        dirpath, filename = os.path.split(path)
        albums[category, dirpath][filename] = captures
    return albums


def synchronize_albums(new_albums, verbosity=0):
    """Synchronize albums from the filesystem to the database.

    `new_albums` is the result of `scan_photo_root`.
    """
    new_keys = set(new_albums.keys())
    old_keys = set((a.category, a.dirpath) for a in Album.objects.all())
    for category, dirpath in sorted(new_keys - old_keys):
        random_capture = new_albums[category, dirpath].itervalues().next()
        date, name = get_album_info(random_capture, verbosity)
        if verbosity >= 1:
            print u"Adding album %s (%s) as %s" % (dirpath, category, name)
        Album.objects.create(category=category, dirpath=dirpath, date=date, name=name)
    for category, dirpath in sorted(old_keys - new_keys):
        if verbosity >= 1:
            print u"Removing album %s (%s)" % (dirpath, category)
        Album.objects.get(category=category, dirpath=dirpath).delete()


def synchronize_photos(new_albums, verbosity=0):
    """Synchronize photos from the filesystem to the database.

    `new_albums` is the result of `scan_photo_root`.
    """
    for (category, dirpath), filenames in new_albums.iteritems():
        album = Album.objects.get(category=category, dirpath=dirpath)
        new_keys = set(filenames.iterkeys())
        old_keys = set(p.filename for p in album.photo_set.all())
        for filename in sorted(new_keys - old_keys):
            date = get_photo_info(new_albums[category, dirpath][filename], verbosity)
            if verbosity >= 2:
                print u"Adding photo %s to album %s (%s)" % (filename, dirpath, category)
            Photo.objects.create(album=album, filename=filename, date=date)
        for filename in sorted(old_keys - new_keys):
            if verbosity >= 2:
                print u"Removing photo %s from album %s (%s)" % (filename, dirpath, category)
            Photo.objects.get(album=album, filename=filename).delete()

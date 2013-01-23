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
    help = 'Scan GALLERY_PHOTO_DIR and update database.'

    @transaction.commit_on_success
    def handle_noargs(self, **options):
        self.verbosity = int(options.get('verbosity', '1'))
        if self.verbosity >= 1:
            t = time.time()
            self.stdout.write(u"Scanning %s\n" % settings.GALLERY_PHOTO_DIR)
        albums = scan_photo_root(self)
        synchronize_albums(albums, self)
        synchronize_photos(albums, self)
        if self.verbosity >= 1:
            dt = time.time() - t
            self.stdout.write(u"Done (%.02fs)\n" % dt)


ignores = [re.compile(i) for i in getattr(settings, 'GALLERY_IGNORES', ())]

def is_ignored(path):
    return any(pat.match(path) for pat in ignores)


patterns = [(cat, re.compile(pat)) for cat, pat in getattr(settings, 'GALLERY_PATTERNS', ())]

def is_matched(path):
    for category, pattern in patterns:
        match = pattern.match(path)
        if match:
            return category, match.groupdict()


fs_encoding = sys.getfilesystemencoding()

def iter_photo_root(command):
    """Yield relative path, category and regex captures for each photo."""
    for dirpath, _, filenames in os.walk(settings.GALLERY_PHOTO_DIR):
        dirpath = dirpath.decode(fs_encoding)
        for filename in filenames:
            filename = filename.decode(fs_encoding)
            filepath = os.path.join(dirpath, filename)
            relpath = os.path.relpath(filepath, settings.GALLERY_PHOTO_DIR)
            if is_ignored(relpath):
                if command.verbosity >= 3:
                    command.stdout.write(u"- %s\n" % relpath)
                continue
            result = is_matched(relpath)
            if result is not None:
                if command.verbosity >= 3:
                    command.stdout.write(u"> %s\n" % relpath)
                category, captures = result
                yield relpath, category, captures
            else:
                if command.verbosity >= 1:
                    command.stderr.write(u"? %s\n" % relpath)


def scan_photo_root(command):
    """Return a dictionary of albums, keyed by (category, dirpath).

    Each album is a dictionary of photos, keyed by filename.

    The result can be passed to synchronize_albums and synchronize_photos.
    """
    albums = collections.defaultdict(lambda: {})
    for path, category, captures in iter_photo_root(command):
        dirpath, filename = os.path.split(path)
        albums[category, dirpath][filename] = captures
    return albums


def get_album_info(captures, command):
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
        if command.verbosity >= 1:
            command.stderr.write(u"%s %s\n" % (e, kwargs))
    name = ' '.join(v for k, v in sorted(captures.iteritems())
                    if k.startswith('a_name') and v is not None)
    name = name.replace(u'/', u' > ')
    return date, name


def get_photo_info(captures, command):
    """Return the datetime of a photo.

    `captures` are elements extracted from the file name of the photo.
    """
    date = None
    try:
        kwargs = dict((k, int(captures['p_' + k]))
                for k in ('year', 'month', 'day', 'hour', 'minute', 'second'))
        date = datetime.datetime(tzinfo=get_default_timezone(), **kwargs)
    except KeyError:
        pass
    except ValueError, e:
        if command.verbosity >= 1:
            command.stderr.write(u"%s %s\n" % (e, kwargs))
    return date


def synchronize_albums(albums, command):
    """Synchronize albums from the filesystem to the database.

    `albums` is the result of `scan_photo_root`.
    """
    new_keys = set(albums.keys())
    old_keys = set((a.category, a.dirpath) for a in Album.objects.all())
    for category, dirpath in sorted(new_keys - old_keys):
        random_capture = albums[category, dirpath].itervalues().next()
        date, name = get_album_info(random_capture, command)
        if command.verbosity >= 1:
            command.stdout.write(u"Adding album %s (%s) as %s\n" % (dirpath, category, name))
        Album.objects.create(category=category, dirpath=dirpath, date=date, name=name)
    for category, dirpath in sorted(old_keys - new_keys):
        if command.verbosity >= 1:
            command.stdout.write(u"Removing album %s (%s)\n" % (dirpath, category))
        Album.objects.get(category=category, dirpath=dirpath).delete()


def synchronize_photos(albums, command):
    """Synchronize photos from the filesystem to the database.

    `albums` is the result of `scan_photo_root`.
    """
    for (category, dirpath), filenames in albums.iteritems():
        album = Album.objects.get(category=category, dirpath=dirpath)
        new_keys = set(filenames.iterkeys())
        old_keys = set(p.filename for p in album.photo_set.all())
        for filename in sorted(new_keys - old_keys):
            date = get_photo_info(albums[category, dirpath][filename], command)
            if command.verbosity >= 2:
                command.stdout.write(u"Adding photo %s to album %s (%s)\n" % (filename, dirpath, category))
            Photo.objects.create(album=album, filename=filename, date=date)
        for filename in sorted(old_keys - new_keys):
            if command.verbosity >= 2:
                command.stdout.write(u"Removing photo %s from album %s (%s)\n" % (filename, dirpath, category))
            Photo.objects.get(album=album, filename=filename).delete()

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
    for _, pat in patterns:
        match = pat.match(path)
        if match:
            return match.groupdict()


def iter_photo_root(verbosity=0):
    for dirpath, _, filenames in os.walk(settings.PHOTO_ROOT):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            relpath = os.path.relpath(filepath, settings.PHOTO_ROOT)
            if is_ignored(relpath):
                if verbosity >= 3:
                    print "-", relpath
                continue
            captures = is_matched(relpath)
            if captures is not None:
                if verbosity >= 3:
                    print ">", relpath
                yield relpath, captures
            else:
                if verbosity >= 2:
                    print "?", relpath


def scan_photo_root(verbosity=0):
    albums = collections.defaultdict(lambda: {})
    for path, captures in iter_photo_root(verbosity):
        dirpath, filename = os.path.split(path)
        dirpath = dirpath.decode(sys.getfilesystemencoding())
        filename = filename.decode(sys.getfilesystemencoding())
        albums[dirpath][filename] = captures
    return albums


def get_album_info(captures, verbosity):
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
    name = ''
    try:
        name = captures['a_name'].replace('/', ' > ')
    except KeyError:
        pass
    return date, name

def get_photo_info(captures, verbosity):
    date = None
    try:
        kwargs = dict((k, int(captures['p_' + k]))
                for k in ('year', 'month', 'day', 'hour', 'minute', 'second'))
        date = datetime.datetime(*kwargs)
    except KeyError:
        pass
    except ValueError, e:
        if verbosity >= 1:
            print e, kwargs
    return date


def synchronize_albums(new_albums, verbosity=0):
    new_dirpaths = set(new_albums.iterkeys())
    old_dirpaths = set(a.dirpath for a in Album.objects.all())
    for dirpath in sorted(new_dirpaths - old_dirpaths):
        if verbosity >= 1:
            print u"Adding album %s" % dirpath
            random_capture = new_albums[dirpath].itervalues().next()
        date, name = get_album_info(random_capture, verbosity)
        Album.objects.create(dirpath=dirpath, date=date, name=name)
    for dirpath in sorted(old_dirpaths - new_dirpaths):
        if verbosity >= 1:
            print u"Removing album %s" % dirpath
        Album.objects.get(dirpath=dirpath).delete()


def synchronize_photos(new_albums, verbosity=0):
    for dirpath, filenames in new_albums.iteritems():
        album = Album.objects.get(dirpath=dirpath)
        new_filenames = set(filenames.iterkeys())
        old_filenames = set(p.filename for p in album.photo_set.all())
        for filename in sorted(new_filenames - old_filenames):
            if verbosity >= 2:
                print u"Adding photo %s to album %s" % (filename, dirpath)
                date = get_photo_info(new_albums[dirpath][filename], verbosity)
                Photo.objects.create(album=album, filename=filename, date=date)
        for filename in sorted(old_filenames - new_filenames):
            if verbosity >= 2:
                print u"Removing photo %s from album %s" % (filename, dirpath)
                Photo.objects.get(album=album, filename=filename).delete()

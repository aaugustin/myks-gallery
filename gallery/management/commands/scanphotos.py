# coding: utf-8

# If you have non-ascii characters in filenames, on Python 2, you may need:
# export PYTHONIOENCODING=utf-8

from __future__ import unicode_literals

import collections
import datetime
import optparse
import os
import re
import time
import unicodedata

import django
from django.conf import settings
from django.core.management import base
from django.db import transaction
from django.utils import timezone

from ...models import Album, Photo
from ...storages import get_storage


class Command(base.BaseCommand):
    help = 'Scan photos and update database.'

    if django.VERSION[:2] >= (1, 8):

        def add_arguments(self, parser):
            parser.add_argument(
                '--full',
                action='store_true',
                dest='full_sync',
                default=False,
                help='Perform a full resynchronization')
            parser.add_argument(
                '--resize',
                action='append',
                dest='resize_presets',
                default=[],
                help='Resize with given preset')

    else:

        option_list = base.BaseCommand.option_list + (
            optparse.make_option(
                '--full',
                action='store_true',
                dest='full_sync',
                default=False,
                help='Perform a full resynchronization'),
            optparse.make_option(
                '--resize',
                action='append',
                dest='resize_presets',
                default=[],
                help='Resize with given preset'),
            )

    @transaction.atomic
    def handle(self, **options):
        self.full_sync = options['full_sync']
        self.resize_presets = options['resize_presets']
        self.verbosity = int(options['verbosity'])

        t = time.time()

        self.write_out("Scanning photos...", verbosity=1)
        albums = scan_photo_storage(self)

        self.write_out("Synchronizing albums...", verbosity=1)
        synchronize_albums(albums, self)

        self.write_out("Synchronizing photos...", verbosity=1)
        synchronize_photos(albums, self)

        dt = time.time() - t
        self.write_out("Done (%.02fs)" % dt, verbosity=1)

    def write_err(self, message, verbosity):
        if self.verbosity >= verbosity:
            self.stderr.write(self.style.ERROR(message + "\n"))

    def write_out(self, message, verbosity):
        if self.verbosity >= verbosity:
            self.stdout.write(message + "\n")


ignores = [re.compile(i) for i in getattr(settings, 'GALLERY_IGNORES', ())]


def is_ignored(path):
    return any(pat.match(path) for pat in ignores)


patterns = [(cat, re.compile(pat)) for cat, pat in getattr(settings, 'GALLERY_PATTERNS', ())]


def is_matched(path):
    for category, pattern in patterns:
        match = pattern.match(path)
        if match:
            return category, match.groupdict()


def walk_photo_storage(storage, path=''):
    """
    Yield (directory path, file names) 2-uples for the photo storage.

    This function directories that do not contain any files.

    """
    directories, files = storage.listdir(path)
    if files:
        yield path, files
    for directory in directories:
        dir_path = os.path.join(path, directory)
        for result in walk_photo_storage(storage, dir_path):
            yield result


def iter_photo_storage(command):
    """
    Yield (relative path, category, regex captures) for each photo.

    """
    photo_storage = get_storage('photo')
    for dirpath, filenames in walk_photo_storage(photo_storage):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            # HFS+ stores names in NFD which causes issues with some fonts.
            filepath = unicodedata.normalize('NFKC', filepath)
            if is_ignored(filepath):
                command.write_out("- %s" % filepath, verbosity=3)
                continue
            result = is_matched(filepath)
            if result is not None:
                command.write_out("> %s" % filepath, verbosity=3)
                category, captures = result
                yield filepath, category, captures
            else:
                command.write_err("? %s" % filepath, verbosity=1)


def scan_photo_storage(command):
    """
    Return a dictionary of albums keyed by (category, dirpath).

    Each album is a dictionary of photos, keyed by filename.

    The result can be passed to ``synchronize_albums`` and
    ``synchronize_photos``.

    """
    albums = collections.defaultdict(lambda: {})
    for path, category, captures in iter_photo_storage(command):
        dirpath, filename = os.path.split(path)
        albums[category, dirpath][filename] = captures
    return albums


def get_album_info(captures, command):
    """
    Return the date and name of an album.

    ``captures`` are elements extracted from the file name of a random photo
    in the album.

    """
    date = None
    try:
        kwargs = {
            k: int(captures['a_' + k])
            for k in ('year', 'month', 'day')
        }
        date = datetime.date(**kwargs)
    except KeyError:
        pass
    except ValueError as e:
        command.write_err("%s %s" % (e, kwargs), verbosity=1)
    name = ' '.join(v for k, v in sorted(captures.items())
                    if k.startswith('a_name') and v is not None)
    name = name.replace('/', ' > ')
    return date, name


def get_photo_info(captures, command):
    """
    Return the datetime of a photo.

    ``captures`` are elements extracted from the file name of the photo.

    """
    date = None
    try:
        kwargs = {
            k: int(captures['p_' + k])
            for k in ('year', 'month', 'day', 'hour', 'minute', 'second')
        }
        date = datetime.datetime(**kwargs)
        if settings.USE_TZ:
            date = timezone.make_aware(date, timezone.get_default_timezone())
    except KeyError:
        pass
    except ValueError as e:
        command.write_err("%s %s" % (e, kwargs), verbosity=1)
    return date


def synchronize_albums(albums, command):
    """
    Synchronize albums from the filesystem to the database.

    ``albums`` is the result of ``scan_photo_storage``.

    """
    new_keys = set(albums.keys())
    old_keys = set((a.category, a.dirpath) for a in Album.objects.all())
    for category, dirpath in sorted(new_keys - old_keys):
        random_capture = next(iter(albums[category, dirpath].values()))
        date, name = get_album_info(random_capture, command)
        command.write_out("Adding album %s (%s) as %s" % (dirpath, category, name), verbosity=1)
        Album.objects.create(category=category, dirpath=dirpath, date=date, name=name)
    for category, dirpath in sorted(old_keys - new_keys):
        command.write_out("Removing album %s (%s)" % (dirpath, category), verbosity=1)
        Album.objects.get(category=category, dirpath=dirpath).delete()


def synchronize_photos(albums, command):
    """
    Synchronize photos from the filesystem to the database.

    ``albums`` is the result of ``scan_photo_storage``.

    """
    for (category, dirpath), filenames in albums.items():
        album = Album.objects.get(category=category, dirpath=dirpath)
        new_keys = set(filenames.keys())
        old_keys = set(p.filename for p in album.photo_set.all())
        for filename in sorted(new_keys - old_keys):
            date = get_photo_info(albums[category, dirpath][filename], command)
            command.write_out(
                "Adding photo %s to album %s (%s)" % (filename, dirpath, category),
                verbosity=2)
            photo = Photo.objects.create(album=album, filename=filename, date=date)
            for preset in command.resize_presets:
                photo.thumbnail(preset)
        for filename in sorted(old_keys - new_keys):
            command.write_out(
                "Removing photo %s from album %s (%s)" % (filename, dirpath, category),
                verbosity=2)
            photo = Photo.objects.get(album=album, filename=filename)
            photo.delete()
        if not command.full_sync:
            continue
        for filename in sorted(old_keys & new_keys):
            date = get_photo_info(albums[category, dirpath][filename], command)
            photo = Photo.objects.get(album=album, filename=filename)
            if date != photo.date:
                command.write_out(
                    "Fixing date of photo %s from album %s (%s)" % (filename, dirpath, category),
                    verbosity=2)
                photo.date = date
                photo.save()

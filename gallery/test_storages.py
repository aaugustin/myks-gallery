# coding: utf-8

from __future__ import unicode_literals

import io

from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage, Storage
from django.test import TestCase
from django.test.utils import override_settings

from .storages import get_storage


class MemoryStorage(Storage):
    """
    Limited implementation of an in-memory file storage.

    This class does the bare minimum for tests to pass. It doesn't implement
    accessed/created/modified_time.

    """
    def __init__(self, *args, **kwargs):
        super(MemoryStorage, self).__init__(*args, **kwargs)
        self.files = {}

    def _open(self, name, mode='rb'):
        assert mode == 'rb'
        return io.BytesIO(self.files[name])

    def _save(self, name, content):
        content = content.read()
        assert isinstance(content, bytes)
        self.files[name] = content
        return name

    def delete(self, name):
        self.files.pop(name, None)

    def exists(self, name):
        return name in self.files

    def listdir(self, name):
        dirs, files = [], []
        for filename in sorted(self.files):
            filename = filename[len(name):]
            if '/' in filename:
                dirs.append(filename.partition('/')[0])
            else:
                files.append(filename)
        return dirs, files

    def size(self, name):
        return len(self.files[name])


class LocalStorage(MemoryStorage):
    """
    Emulates a storage class that stores files on disk.

    """
    def path(self, name):
        return '/path/to/' + name


class RemoteStorage(MemoryStorage):
    """
    Emulates a storage class that stores files in memory.

    """
    def url(self, name):
        return '/url/of/' + name


class StoragesTest(TestCase):

    @override_settings(GALLERY_FOO_STORAGE='gallery.test_storages.MemoryStorage')
    def test_get_storage(self):
        foo_storage = get_storage('foo')
        self.assertIsInstance(foo_storage, MemoryStorage)

    @override_settings(GALLERY_FOO_STORAGE='gallery.test_storages.MemoryStorage')
    def test_get_storage_caching(self):
        foo_storage_1 = get_storage('foo')
        foo_storage_2 = get_storage('foo')
        self.assertIs(foo_storage_1, foo_storage_2)

    @override_settings(GALLERY_FOO_DIR='/path/to/foo')
    def test_get_storage_legacy(self):
        foo_storage = get_storage('foo')
        self.assertIsInstance(foo_storage, FileSystemStorage)
        self.assertEqual(foo_storage.location, '/path/to/foo')

    def test_get_storage_unconfigured(self):
        with self.assertRaises(ImproperlyConfigured):
            get_storage('foo')

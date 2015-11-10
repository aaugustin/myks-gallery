# coding: utf-8

from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage
from django.test import TestCase
from django.test.utils import override_settings

from .storages import get_storage


class FooStorage(object):
    pass


class StoragesTest(TestCase):

    @override_settings(GALLERY_FOO_STORAGE='gallery.test_storages.FooStorage')
    def test_get_storage(self):
        foo_storage = get_storage('foo')
        self.assertIsInstance(foo_storage, FooStorage)

    @override_settings(GALLERY_FOO_STORAGE='gallery.test_storages.FooStorage')
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


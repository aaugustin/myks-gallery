import io
import urllib.parse

from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import Storage
from django.test import TestCase

from .storages import get_storage


class MemoryStorage(Storage):  # pragma: no cover
    """
    Limited implementation of an in-memory file storage.

    This class does the bare minimum for tests to pass. It doesn't implement
    accessed/created/modified_time.

    It doesn't provide a ``path()`` method. Its ``url()`` method returns
    ``/url/of`` followed by the file name.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.files = {}

    def _open(self, name, mode="rb"):
        assert mode == "rb"
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
            filename = filename[len(name) :]
            if "/" in filename:
                dirs.append(filename.partition("/")[0])
            else:
                files.append(filename)
        return dirs, files

    def size(self, name):
        return len(self.files[name])

    def url(self, name):
        return "/url/of/" + urllib.parse.quote(name)


class StoragesTest(TestCase):
    def test_get_storage(self):
        with self.settings(GALLERY_FOO_STORAGE="gallery.test_storages.MemoryStorage"):
            foo_storage = get_storage("foo")
        self.assertIsInstance(foo_storage, MemoryStorage)

    def test_get_storage_caching(self):
        with self.settings(GALLERY_FOO_STORAGE="gallery.test_storages.MemoryStorage"):
            foo_storage_1 = get_storage("foo")
            foo_storage_2 = get_storage("foo")
        self.assertIs(foo_storage_1, foo_storage_2)

    def test_get_storage_unconfigured(self):
        with self.assertRaises(ImproperlyConfigured):
            get_storage("foo")

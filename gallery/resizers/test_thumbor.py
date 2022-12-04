from django.test import TestCase

from ..models import Album, Photo
from .thumbor import resize


class ResizeTests(TestCase):
    def setUp(self):
        super().setUp()
        self.album = Album(category="default", dirpath="album")
        self.photo = Photo(album=self.album, filename="original.jpg")

    def test_resize(self):
        self.assertEqual(
            resize(self.photo, 128, 128, True),
            "http://localhost:8888/UqYbfk-dJ8uNobtFuKVzxIwKCsA=/128x128/smart/album/original.jpg",  # noqa
        )

    def test_resize_no_crop(self):
        self.assertEqual(
            resize(self.photo, 128, 128, False),
            "http://localhost:8888/VKEUnVMAgbzCbjfBfwvEEM3UzGI=/fit-in/128x128/smart/album/original.jpg",  # noqa
        )

# coding: utf-8

from __future__ import unicode_literals

import io

from django.test import TestCase
from django.test.utils import override_settings
from PIL import Image, ImageDraw

from .imgutil import make_thumbnail
from .test_storages import MemoryStorage


def make_image(storage, name, width, height, format='JPEG', mode='RGB'):
    """
    Utility function to create an image for testing.

    """
    im = Image.new(mode, (width, height))
    draw = ImageDraw.Draw(im)
    draw.rectangle([0, 0, width // 2, height // 2], '#F00')
    draw.rectangle([width // 2, 0, width, height // 2], '#0F0')
    draw.rectangle([0, height // 2, width // 2, height], '#00F')
    draw.rectangle([width // 2, height // 2, width, height], '#000')
    draw.rectangle([width // 4, height // 4, 3 * width // 4, 3 * height // 4], '#FFF')
    im_bytes_io = io.BytesIO()
    im.save(im_bytes_io, format)
    im_bytes_io.seek(0)
    storage.save(name, im_bytes_io)


@override_settings(GALLERY_RESIZE_PRESETS={
    'thumbnail': (8, 8, True),
    'preview': (16, 16, False),
})
class ThumbnailTests(TestCase):

    def setUp(self):
        super(ThumbnailTests, self).setUp()
        self.storage = MemoryStorage()

    def make_image(self, width, height,
                   image_name='original.jpg', format='JPEG', mode='RGB'):
        make_image(self.storage, image_name, width, height, format, mode)

    def make_thumbnail(self, preset,
                       image_name='original.jpg', thumb_name='thumbnail.jpg'):
        make_thumbnail(image_name, thumb_name, preset,
                       self.storage, self.storage)

    def open_image(self, thumb_name='thumbnail.jpg'):
        return Image.open(self.storage.open(thumb_name))

    def test_horizontal_thumbnail(self):
        self.make_image(48, 36)
        self.make_thumbnail('thumbnail')

        im = self.open_image()
        self.assertEqual(im.size, (8, 8))

    def test_horizontal_preview(self):
        self.make_image(48, 36)
        self.make_thumbnail('preview')

        im = self.open_image()
        self.assertEqual(im.size, (16, 12))

    def test_square_thumbnail(self):
        self.make_image(36, 36)
        self.make_thumbnail('thumbnail')

        im = self.open_image()
        self.assertEqual(im.size, (8, 8))

    def test_square_preview(self):
        self.make_image(36, 36)
        self.make_thumbnail('preview')

        im = self.open_image()
        self.assertEqual(im.size, (16, 16))

    def test_vertical_thumbnail(self):
        self.make_image(36, 48)
        self.make_thumbnail('thumbnail')

        im = self.open_image()
        self.assertEqual(im.size, (8, 8))

    def test_vertical_preview(self):
        self.make_image(36, 48)
        self.make_thumbnail('preview')

        im = self.open_image()
        self.assertEqual(im.size, (12, 16))

    def test_non_jpg_thumbnail(self):
        self.make_image(36, 36, 'original.png', 'PNG')
        self.make_thumbnail('thumbnail', 'original.png', 'thumbnail.png')

        im = self.open_image('thumbnail.png')
        self.assertEqual(im.format, 'PNG')
        self.assertEqual(im.size, (8, 8))

# coding: utf-8

from __future__ import unicode_literals

import io
import os

from PIL import Image
from PIL import ImageDraw

from django.core.files.storage import FileSystemStorage
from django.test import TestCase
from django.test.utils import override_settings

from .imgutil import make_thumbnail
from .test_storages import MemoryStorage


def make_image(storage, name, width, height, format='JPEG', mode='RGB'):
    """
    Utility function to create an image for testing.

    """
    im = Image.new(mode, (width, height))
    draw = ImageDraw.Draw(im)
    for x in range(width):
        draw.line([(x, 0), (x, height - 1)], fill="hsl(%d,100%%,50%%)" % x)
    im_bytes_io = io.BytesIO()
    im.save(im_bytes_io, format)
    im_bytes_io.seek(0)
    storage.save(name, im_bytes_io)


@override_settings(GALLERY_RESIZE_PRESETS={
    'thumbnail': (60, 60, True),
    'preview': (120, 120, False),
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
        self.make_image(360, 240)
        self.make_thumbnail('thumbnail')

        im = self.open_image()
        self.assertEqual(im.size, (60, 60))

    def test_horizontal_preview(self):
        self.make_image(360, 240)
        self.make_thumbnail('preview')

        im = self.open_image()
        self.assertEqual(im.size, (120, 80))

    def test_square_thumbnail(self):
        self.make_image(240, 240)
        self.make_thumbnail('thumbnail')

        im = self.open_image()
        self.assertEqual(im.size, (60, 60))

    def test_square_preview(self):
        self.make_image(240, 240)
        self.make_thumbnail('preview')

        im = self.open_image()
        self.assertEqual(im.size, (120, 120))

    def test_vertical_thumbnail(self):
        self.make_image(240, 360)
        self.make_thumbnail('thumbnail')

        im = self.open_image()
        self.assertEqual(im.size, (60, 60))

    def test_vertical_preview(self):
        self.make_image(240, 360)
        self.make_thumbnail('preview')

        im = self.open_image()
        self.assertEqual(im.size, (80, 120))

    def test_non_jpg_thumbnail(self):
        self.make_image(240, 240, 'original.png', 'PNG')
        self.make_thumbnail('thumbnail','original.png', 'thumbnail.png')

        im = self.open_image('thumbnail.png')
        self.assertEqual(im.format, 'PNG')
        self.assertEqual(im.size, (60, 60))

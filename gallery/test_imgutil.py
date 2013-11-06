# coding: utf-8
# Copyright (c) 2013 Aymeric Augustin. All rights reserved.

from __future__ import unicode_literals

import os
import shutil
import tempfile

try:
    from PIL import Image
    from PIL import ImageDraw
except ImportError:                                         # pragma: no cover
    import Image
    import ImageDraw

from django.test import TestCase
from django.test.utils import override_settings

from .imgutil import make_thumbnail


class ThumbnailsMixin(object):

    def setUp(self):
        super(ThumbnailsMixin, self).setUp()
        self.tmpdir = tempfile.mkdtemp()
        self.original = os.path.join(self.tmpdir, 'original.jpg')
        self.thumbnail = os.path.join(self.tmpdir, 'thumbnail.jpg')

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        super(ThumbnailsMixin, self).tearDown()

    def make_image(self, width, height, format='JPEG', mode='RGB'):
        im = Image.new(mode, (width, height))
        draw = ImageDraw.Draw(im)
        for x in range(width):
            draw.line([(x, 0), (x, height - 1)], fill="hsl(%d,100%%,50%%)" % x)
        im.save(self.original, format)


@override_settings(GALLERY_RESIZE_PRESETS={
    'thumbnail': (60, 60, True),
    'preview': (120, 120, False),
})
class ThumbnailTests(ThumbnailsMixin, TestCase):

    def test_horizontal_thumbnail(self):
        self.make_image(360, 240)
        make_thumbnail(self.original, self.thumbnail, 'thumbnail')

        im = Image.open(self.thumbnail)
        self.assertEqual(im.size, (60, 60))

    def test_horizontal_preview(self):
        self.make_image(360, 240)
        make_thumbnail(self.original, self.thumbnail, 'preview')

        im = Image.open(self.thumbnail)
        self.assertEqual(im.size, (120, 80))

    def test_square_thumbnail(self):
        self.make_image(240, 240)
        make_thumbnail(self.original, self.thumbnail, 'thumbnail')

        im = Image.open(self.thumbnail)
        self.assertEqual(im.size, (60, 60))

    def test_square_preview(self):
        self.make_image(240, 240)
        make_thumbnail(self.original, self.thumbnail, 'preview')

        im = Image.open(self.thumbnail)
        self.assertEqual(im.size, (120, 120))

    def test_vertical_thumbnail(self):
        self.make_image(240, 360)
        make_thumbnail(self.original, self.thumbnail, 'thumbnail')

        im = Image.open(self.thumbnail)
        self.assertEqual(im.size, (60, 60))

    def test_vertical_preview(self):
        self.make_image(240, 360)
        make_thumbnail(self.original, self.thumbnail, 'preview')

        im = Image.open(self.thumbnail)
        self.assertEqual(im.size, (80, 120))

    def test_create_directory(self):
        self.make_image(360, 240)
        self.thumbnail = os.path.join(self.tmpdir, 'subdir', 'thumbnail.jpg')
        make_thumbnail(self.original, self.thumbnail, 'thumbnail')

    def test_non_jpg_thumbnail(self):
        self.original = self.original[:-3] + 'png'
        self.thumbnail = self.thumbnail[:-3] + 'png'

        self.make_image(240, 240, 'PNG')
        make_thumbnail(self.original, self.thumbnail, 'thumbnail')

        im = Image.open(self.thumbnail)
        self.assertEqual(im.format, 'PNG')
        self.assertEqual(im.size, (60, 60))

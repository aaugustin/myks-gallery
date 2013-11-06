# coding: utf-8
# Copyright (c) 2011-2012 Aymeric Augustin. All rights reserved.

from __future__ import division
from __future__ import unicode_literals

import os
import sys

try:
    from PIL import Image
    from PIL import ImageFile
except ImportError:                                         # pragma: no cover
    import Image
    import ImageFile

from django.conf import settings
from django.utils import six


exif_rotations = (                                          # pragma: no cover
    None,
    lambda image: image,
    lambda image: image.transpose(Image.FLIP_LEFT_RIGHT),
    lambda image: image.transpose(Image.ROTATE_180),
    # shortcut for image.transpose(Image.ROTATE_180).transpose(FLIP_LEFT_RIGHT)
    lambda image: image.transpose(Image.FLIP_TOP_BOTTOM),
    lambda image: image.transpose(Image.ROTATE_270).transpose(Image.FLIP_LEFT_RIGHT),
    lambda image: image.transpose(Image.ROTATE_270),
    lambda image: image.transpose(Image.ROTATE_90).transpose(Image.FLIP_LEFT_RIGHT),
    lambda image: image.transpose(Image.ROTATE_90),
)


fs_encoding = sys.getfilesystemencoding()

def make_thumbnail(image_path, thumb_path, preset):
    options = getattr(settings, 'GALLERY_RESIZE_OPTIONS', {})
    presets = getattr(settings, 'GALLERY_RESIZE_PRESETS', {})

    if six.PY2:
        image_path = image_path.encode(fs_encoding)
        thumb_path = thumb_path.encode(fs_encoding)

    image = Image.open(image_path)

    if image.format == 'JPEG':
        # Auto-rotate JPEG files based on EXIF information
        try:                                                # pragma: no cover
            # Use of an undocumented API — let's catch exceptions liberally
            orientation = image._getexif()[274]
            image = exif_rotations[orientation](image)
        except Exception:
            pass

        # Increase PIL's output buffer from 64k to 4MB to avoid JPEG save errors
        ImageFile.MAXBLOCK = 4194304

    # Pre-crop if requested and the aspect ratios don't match exactly
    image_width, image_height = image.size
    thumb_width, thumb_height, crop = presets[preset]
    if crop:
        if thumb_width * image_height > image_width * thumb_height:
            target_height = image_width * thumb_height // thumb_width
            top = (image_height - target_height) // 2
            image = image.crop((0, top, image_width, top + target_height))
        elif thumb_width * image_height < image_width * thumb_height:
            target_width = image_height * thumb_width // thumb_height
            left = (image_width - target_width) // 2
            image = image.crop((left, 0, left + target_width, image_height))

    # Save the thumbnail
    image.thumbnail((thumb_width, thumb_height), Image.ANTIALIAS)
    try:
        if not os.path.isdir(os.path.dirname(thumb_path)):
            os.makedirs(os.path.dirname(thumb_path))
        image.save(thumb_path, **options.get(image.format, {}))
    except IOError:                                         # pragma: no cover
        try:
            os.unlink(thumb_path)
        except OSError:
            pass
        raise

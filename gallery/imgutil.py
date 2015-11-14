# coding: utf-8

from __future__ import division, unicode_literals

import io

from django.conf import settings
from PIL import Image, ImageFile

exif_rotations = [                                          # pragma: no cover
    None,
    lambda image: image,
    lambda image: image.transpose(Image.FLIP_LEFT_RIGHT),
    lambda image: image.transpose(Image.ROTATE_180),
    # shortcut for image.transpose(Image.ROTATE_180).transpose(FLIP_LEFT_RIGHT)
    lambda image: image.transpose(Image.FLIP_TOP_BOTTOM),
    lambda image: image.transpose(Image.ROTATE_270).transpose(Image.FLIP_LEFT_RIGHT),   # noqa
    lambda image: image.transpose(Image.ROTATE_270),
    lambda image: image.transpose(Image.ROTATE_90).transpose(Image.FLIP_LEFT_RIGHT),    # noqa
    lambda image: image.transpose(Image.ROTATE_90),
]


def make_thumbnail(image_name, thumb_name, preset,
                   image_storage, thumb_storage):

    options = getattr(settings, 'GALLERY_RESIZE_OPTIONS', {})
    presets = getattr(settings, 'GALLERY_RESIZE_PRESETS', {})

    # Load the image
    image = Image.open(image_storage.open(image_name))
    format = image.format

    if format == 'JPEG':
        # Auto-rotate JPEG files based on EXIF information
        try:                                                # pragma: no cover
            # Use of an undocumented API — let's catch exceptions liberally
            orientation = image._getexif()[274]
            image = exif_rotations[orientation](image)
        except Exception:
            pass

        # Increase Pillow's buffer from 64k to 4MB to avoid JPEG save errors
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

    # Resize
    image.thumbnail((thumb_width, thumb_height), Image.ANTIALIAS)

    # Save the thumbnail
    thumb_bytes_io = io.BytesIO()
    image.save(thumb_bytes_io, format, **options.get(image.format, {}))
    thumb_bytes_io.seek(0)
    thumb_storage.save(thumb_name, thumb_bytes_io)

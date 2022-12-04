import datetime
import io

from django.test import TestCase
from PIL import Image, ImageDraw

from ..models import Album, Photo
from ..storages import get_storage
from ..test_storages import MemoryStorage
from .pillow import make_thumbnail, resize


def make_image(name, width, height, storage, *, format="JPEG", mode="RGB"):
    """
    Utility function to create an image for testing.

    """
    im = Image.new(mode, (width, height))
    draw = ImageDraw.Draw(im)
    draw.rectangle([0, 0, width // 2, height // 2], "#F00")
    draw.rectangle([width // 2, 0, width, height // 2], "#0F0")
    draw.rectangle([0, height // 2, width // 2, height], "#00F")
    draw.rectangle([width // 2, height // 2, width, height], "#000")
    draw.rectangle([width // 4, height // 4, 3 * width // 4, 3 * height // 4], "#FFF")
    im_bytes_io = io.BytesIO()
    im.save(im_bytes_io, format)
    im_bytes_io.seek(0)
    storage.save(name, im_bytes_io)


class ResizeTests(TestCase):
    def setUp(self):
        super().setUp()
        date = datetime.date(2023, 1, 1)
        self.album = Album(category="default", dirpath="album", date=date)
        self.photo = Photo(album=self.album, filename="original.jpg")
        make_image(self.photo.image_name, 48, 36, get_storage("photo"))

    def test_resize(self):
        thumb_name = "2301/9b35d14e151f31cf363cd9c1c1342b1f.jpg"
        self.assertEqual(resize(self.photo, 16, 16, True), f"/url/of/{thumb_name}")

        im = Image.open(get_storage("cache").open(thumb_name))
        self.assertEqual(im.size, (16, 16))


class ThumbnailTests(TestCase):
    def setUp(self):
        super().setUp()
        self.storage = MemoryStorage()

    def make_image(
        self, width, height, image_name="original.jpg", format="JPEG", mode="RGB"
    ):
        make_image(image_name, width, height, self.storage, format=format, mode=mode)

    def make_thumbnail(
        self, width, height, crop, image_name="original.jpg", thumb_name="thumbnail.jpg"
    ):
        make_thumbnail(
            image_name, thumb_name, width, height, crop, self.storage, self.storage
        )

    def open_image(self, thumb_name="thumbnail.jpg"):
        return Image.open(self.storage.open(thumb_name))

    def test_horizontal_thumbnail(self):
        self.make_image(48, 36)
        self.make_thumbnail(8, 8, True)

        im = self.open_image()
        self.assertEqual(im.size, (8, 8))

    def test_horizontal_preview(self):
        self.make_image(48, 36)
        self.make_thumbnail(16, 16, False)

        im = self.open_image()
        self.assertEqual(im.size, (16, 12))

    def test_square_thumbnail(self):
        self.make_image(36, 36)
        self.make_thumbnail(8, 8, True)

        im = self.open_image()
        self.assertEqual(im.size, (8, 8))

    def test_square_preview(self):
        self.make_image(36, 36)
        self.make_thumbnail(16, 16, False)

        im = self.open_image()
        self.assertEqual(im.size, (16, 16))

    def test_vertical_thumbnail(self):
        self.make_image(36, 48)
        self.make_thumbnail(8, 8, True)

        im = self.open_image()
        self.assertEqual(im.size, (8, 8))

    def test_vertical_preview(self):
        self.make_image(36, 48)
        self.make_thumbnail(16, 16, False)

        im = self.open_image()
        self.assertEqual(im.size, (12, 16))

    def test_non_jpg_thumbnail(self):
        self.make_image(36, 36, "original.png", "PNG")
        self.make_thumbnail(8, 8, True, "original.png", "thumbnail.png")

        im = self.open_image("thumbnail.png")
        self.assertEqual(im.format, "PNG")
        self.assertEqual(im.size, (8, 8))

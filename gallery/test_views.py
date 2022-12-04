import datetime
import zipfile

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse

from .models import Album, AlbumAccessPolicy, Photo
from .resizers.pillow import get_resized_name
from .resizers.test_pillow import make_image
from .storages import get_storage


class ViewsTestsMixin:
    def make_image(self):
        make_image(self.photo.image_name, 48, 36, get_storage("photo"))

    def test_index_view(self):
        response = self.client.get(reverse("gallery:index"))
        self.assertTemplateUsed(response, "gallery/album_archive.html")

    def test_search_view(self):
        response = self.client.get(reverse("gallery:index"), {"q": "original"})
        self.assertTemplateUsed(response, "gallery/album_archive.html")

    def test_year_view(self):
        response = self.client.get(reverse("gallery:year", args=[self.album.date.year]))
        self.assertTemplateUsed(response, "gallery/album_archive_year.html")

    def test_album_view(self):
        response = self.client.get(reverse("gallery:album", args=[self.album.pk]))
        self.assertTemplateUsed(response, "gallery/album_detail.html")

    def test_photo_view(self):
        response = self.client.get(reverse("gallery:photo", args=[self.photo.pk]))
        self.assertTemplateUsed(response, "gallery/photo_detail.html")

    def test_album_export_view(self):
        self.make_image()
        url = reverse("gallery:album-export", args=[self.album.pk])
        response = self.client.get(url)
        self.assertTrue(response["Location"].startswith("/url/of/export/"))
        export_file = response["Location"][len("/url/of/") :]
        with zipfile.ZipFile(get_storage("cache").open(export_file)) as archive:
            self.assertEqual(archive.namelist(), ["original.jpg"])

    def test_photo_resized_view(self):
        with self.settings(GALLERY_RESIZE_PRESETS={"resized": (120, 120, False)}):
            self.make_image()
            url = reverse("gallery:photo-resized", args=["resized", self.photo.pk])
            response = self.client.get(url)
            resized_name = get_resized_name(self.photo, 120, 120, False)
            self.assertRedirects(
                response, "/url/of/" + resized_name, fetch_redirect_response=False
            )

    def test_photo_original_view(self):
        self.make_image()
        url = reverse("gallery:photo-original", args=[self.photo.pk])
        response = self.client.get(url)
        self.assertRedirects(
            response, "/url/of/" + self.photo.image_name, fetch_redirect_response=False
        )

    def test_latest_view(self):
        response = self.client.get(reverse("gallery:latest"))
        self.assertRedirects(response, reverse("gallery:album", args=[self.album.pk]))
        self.album.delete()
        response = self.client.get(reverse("gallery:latest"))
        self.assertRedirects(response, reverse("gallery:index"))


class ViewsWithPermissionTests(ViewsTestsMixin, TestCase):
    def setUp(self):
        super().setUp()
        today = datetime.date.today()
        self.album = Album.objects.create(
            category="default", dirpath="album", date=today
        )
        self.photo = Photo.objects.create(album=self.album, filename="original.jpg")
        self.user = User.objects.create_user("user", "user@gallery", "pass")
        self.user.user_permissions.add(Permission.objects.get(codename="view"))
        self.client.login(username="user", password="pass")


class ViewsWithPrivateAccessPolicyTests(ViewsTestsMixin, TestCase):
    def setUp(self):
        super().setUp()
        today = datetime.date.today()
        self.album = Album.objects.create(
            category="default", dirpath="album", date=today
        )
        AlbumAccessPolicy.objects.create(album=self.album, public=False, inherit=True)
        self.photo = Photo.objects.create(album=self.album, filename="original.jpg")
        self.user = User.objects.create_user("user", "user@gallery", "pass")
        self.album.access_policy.users.add(self.user)
        self.client.login(username="user", password="pass")

    def test_hide_private_albums(self):
        self.client.logout()
        response = self.client.get(reverse("gallery:index"))
        self.assertQuerysetEqual(response.context["latest"], [])


class ViewsWithPublicAccessPolicyTests(ViewsTestsMixin, TestCase):
    def setUp(self):
        super().setUp()
        today = datetime.date.today()
        self.album = Album.objects.create(
            category="default", dirpath="album", date=today
        )
        AlbumAccessPolicy.objects.create(album=self.album, public=True, inherit=True),
        self.photo = Photo.objects.create(album=self.album, filename="original.jpg")

    def test_show_and_hide_public_albums(self):
        # Public albums are shown for anonymous users
        response = self.client.get(reverse("gallery:index"))
        self.assertQuerysetEqual(
            response.context["latest"], [self.album], transform=lambda a: a
        )

        # By default public albums are hidden for authenticated users
        self.user = User.objects.create_user("user", "user@gallery", "pass")
        self.client.login(username="user", password="pass")
        response = self.client.get(reverse("gallery:index"))
        self.assertQuerysetEqual(response.context["latest"], [])

        # Showing public albums is persistent
        response = self.client.get(reverse("gallery:index") + "?show_public")
        self.assertQuerysetEqual(
            response.context["latest"], [self.album], transform=lambda a: a
        )
        response = self.client.get(reverse("gallery:index"))
        self.assertQuerysetEqual(
            response.context["latest"], [self.album], transform=lambda a: a
        )

        # Hiding public albums is persistent
        response = self.client.get(reverse("gallery:index") + "?hide_public")
        self.assertQuerysetEqual(response.context["latest"], [])
        response = self.client.get(reverse("gallery:index"))
        self.assertQuerysetEqual(response.context["latest"], [])

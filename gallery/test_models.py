import datetime

from django.contrib.auth.models import Group, User
from django.test import TestCase

from .models import Album, AlbumAccessPolicy, Photo, PhotoAccessPolicy


class AccessPolicyTests(TestCase):

    def setUp(self):
        today = datetime.date.today()
        self.album = Album.objects.create(category='default', dirpath='foo', date=today)
        self.photo = Photo.objects.create(album=self.album, filename='bar')
        self.group = Group.objects.create(name='group')
        self.user = User.objects.create_user('user', 'user@gallery', 'pass')
        self.user.groups.add(self.group)
        self.other = User.objects.create_user('other', 'other@gallery', 'word')

    def assertAlbumAllowedFor(self, user):
        self.assertTrue(self.album.is_allowed_for_user(user))
        self.assertQuerysetEqual(
            Album.objects.allowed_for_user(user),
            [self.album.id],
            lambda album: album.id,
        )

    def assertAlbumNotAllowedFor(self, user):
        self.assertFalse(self.album.is_allowed_for_user(user))
        self.assertQuerysetEqual(
            Album.objects.allowed_for_user(user),
            [],
            lambda album: album.id,
        )

    def assertPhotoAllowedFor(self, user):
        self.assertTrue(self.photo.is_allowed_for_user(user))
        self.assertQuerysetEqual(
            Photo.objects.allowed_for_user(user),
            [self.photo.id],
            lambda photo: photo.id,
        )

    def assertPhotoNotAllowedFor(self, user):
        self.assertFalse(self.photo.is_allowed_for_user(user))
        self.assertQuerysetEqual(
            Photo.objects.allowed_for_user(user),
            [],
            lambda photo: photo.id,
        )

    def test_private_album(self):
        self.assertAlbumNotAllowedFor(self.user)

    def test_public_album(self):
        AlbumAccessPolicy.objects.create(album=self.album, public=True)
        self.assertAlbumAllowedFor(self.user)

    def test_user_album(self):
        policy = AlbumAccessPolicy.objects.create(album=self.album, public=False)
        policy.users.add(self.user)
        self.assertAlbumAllowedFor(self.user)
        self.assertAlbumNotAllowedFor(self.other)

    def test_group_album(self):
        policy = AlbumAccessPolicy.objects.create(album=self.album, public=False)
        policy.groups.add(self.group)
        self.assertAlbumAllowedFor(self.user)
        self.assertAlbumNotAllowedFor(self.other)

    def test_private_photo(self):
        self.assertPhotoNotAllowedFor(self.user)

    def test_public_photo(self):
        PhotoAccessPolicy.objects.create(photo=self.photo, public=True)
        self.assertPhotoAllowedFor(self.user)

    def test_user_photo(self):
        policy = PhotoAccessPolicy.objects.create(photo=self.photo, public=False)
        policy.users.add(self.user)
        self.assertPhotoAllowedFor(self.user)
        self.assertPhotoNotAllowedFor(self.other)

    def test_group_photo(self):
        policy = PhotoAccessPolicy.objects.create(photo=self.photo, public=False)
        policy.groups.add(self.group)
        self.assertPhotoAllowedFor(self.user)
        self.assertPhotoNotAllowedFor(self.other)

    def test_public_photo_inherit(self):
        AlbumAccessPolicy.objects.create(album=self.album, public=True)
        self.assertPhotoAllowedFor(self.user)

    def test_user_photo_inherit(self):
        policy = AlbumAccessPolicy.objects.create(album=self.album, public=False)
        policy.users.add(self.user)
        self.assertPhotoAllowedFor(self.user)
        self.assertPhotoNotAllowedFor(self.other)

    def test_group_photo_inherit(self):
        policy = AlbumAccessPolicy.objects.create(album=self.album, public=False)
        policy.groups.add(self.group)
        self.assertPhotoAllowedFor(self.user)
        self.assertPhotoNotAllowedFor(self.other)

    def test_public_photo_no_inherit(self):
        AlbumAccessPolicy.objects.create(album=self.album, inherit=False, public=True)
        self.assertPhotoNotAllowedFor(self.user)
        PhotoAccessPolicy.objects.create(photo=self.photo, public=True)
        self.assertPhotoAllowedFor(self.user)

    def test_user_photo_no_inherit(self):
        policy = AlbumAccessPolicy.objects.create(album=self.album, inherit=False, public=False)
        policy.users.add(self.user)
        self.assertPhotoNotAllowedFor(self.user)
        self.assertPhotoNotAllowedFor(self.other)
        policy = PhotoAccessPolicy.objects.create(photo=self.photo, public=False)
        policy.users.add(self.user)
        self.assertPhotoAllowedFor(self.user)
        self.assertPhotoNotAllowedFor(self.other)

    def test_group_photo_no_inherit(self):
        policy = AlbumAccessPolicy.objects.create(album=self.album, inherit=False, public=False)
        policy.groups.add(self.group)
        self.assertPhotoNotAllowedFor(self.user)
        self.assertPhotoNotAllowedFor(self.other)
        policy = PhotoAccessPolicy.objects.create(photo=self.photo, public=False)
        policy.groups.add(self.group)
        self.assertPhotoAllowedFor(self.user)
        self.assertPhotoNotAllowedFor(self.other)

    def test_public_photo_counter_inherit(self):
        AlbumAccessPolicy.objects.create(album=self.album, inherit=True, public=True)
        self.assertPhotoAllowedFor(self.user)
        PhotoAccessPolicy.objects.create(photo=self.photo, public=False)
        self.assertPhotoNotAllowedFor(self.user)

    def test_user_photo_counter_inherit(self):
        policy = AlbumAccessPolicy.objects.create(album=self.album, inherit=True, public=False)
        policy.users.add(self.user)
        self.assertPhotoAllowedFor(self.user)
        self.assertPhotoNotAllowedFor(self.other)
        PhotoAccessPolicy.objects.create(photo=self.photo, public=False)
        self.assertPhotoNotAllowedFor(self.user)
        self.assertPhotoNotAllowedFor(self.other)

    def test_group_photo_counter_inherit(self):
        policy = AlbumAccessPolicy.objects.create(album=self.album, inherit=True, public=False)
        policy.groups.add(self.group)
        self.assertPhotoAllowedFor(self.user)
        self.assertPhotoNotAllowedFor(self.other)
        PhotoAccessPolicy.objects.create(photo=self.photo, public=False)
        self.assertPhotoNotAllowedFor(self.user)
        self.assertPhotoNotAllowedFor(self.other)

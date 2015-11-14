# coding: utf-8

from __future__ import unicode_literals

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

    def test_private_album(self):
        self.assertFalse(self.album.is_allowed_for_user(self.user))

    def test_public_album(self):
        AlbumAccessPolicy.objects.create(album=self.album, public=True)
        self.assertTrue(self.album.is_allowed_for_user(self.user))

    def test_user_album(self):
        policy = AlbumAccessPolicy.objects.create(album=self.album, public=False)
        policy.users.add(self.user)
        self.assertTrue(self.album.is_allowed_for_user(self.user))
        self.assertFalse(self.album.is_allowed_for_user(self.other))

    def test_group_album(self):
        policy = AlbumAccessPolicy.objects.create(album=self.album, public=False)
        policy.groups.add(self.group)
        self.assertTrue(self.album.is_allowed_for_user(self.user))
        self.assertFalse(self.album.is_allowed_for_user(self.other))

    def test_user_group_album(self):
        policy = AlbumAccessPolicy.objects.create(album=self.album, public=False)
        policy.groups.add(self.group)
        policy.users.add(self.other)
        self.assertTrue(self.album.is_allowed_for_user(self.user))
        self.assertTrue(self.album.is_allowed_for_user(self.other))

    def test_private_photo(self):
        self.assertFalse(self.photo.is_allowed_for_user(self.user))

    def test_public_photo(self):
        PhotoAccessPolicy.objects.create(photo=self.photo, public=True)
        self.assertTrue(self.photo.is_allowed_for_user(self.user))

    def test_user_photo(self):
        policy = PhotoAccessPolicy.objects.create(photo=self.photo, public=False)
        policy.users.add(self.user)
        self.assertTrue(self.photo.is_allowed_for_user(self.user))
        self.assertFalse(self.photo.is_allowed_for_user(self.other))

    def test_group_photo(self):
        policy = PhotoAccessPolicy.objects.create(photo=self.photo, public=False)
        policy.groups.add(self.group)
        self.assertTrue(self.photo.is_allowed_for_user(self.user))
        self.assertFalse(self.photo.is_allowed_for_user(self.other))

    def test_user_group_photo(self):
        policy = PhotoAccessPolicy.objects.create(photo=self.photo, public=False)
        policy.groups.add(self.group)
        policy.users.add(self.other)
        self.assertTrue(self.photo.is_allowed_for_user(self.user))
        self.assertTrue(self.photo.is_allowed_for_user(self.other))

    def test_public_photo_inherit(self):
        AlbumAccessPolicy.objects.create(album=self.album, public=True)
        self.assertTrue(self.photo.is_allowed_for_user(self.user))

    def test_user_photo_inherit(self):
        policy = AlbumAccessPolicy.objects.create(album=self.album, public=False)
        policy.users.add(self.user)
        self.assertTrue(self.photo.is_allowed_for_user(self.user))
        self.assertFalse(self.photo.is_allowed_for_user(self.other))

    def test_group_photo_inherit(self):
        policy = AlbumAccessPolicy.objects.create(album=self.album, public=False)
        policy.groups.add(self.group)
        self.assertTrue(self.photo.is_allowed_for_user(self.user))
        self.assertFalse(self.photo.is_allowed_for_user(self.other))

    def test_user_group_photo_inherit(self):
        policy = AlbumAccessPolicy.objects.create(album=self.album, public=False)
        policy.groups.add(self.group)
        policy.users.add(self.other)
        self.assertTrue(self.photo.is_allowed_for_user(self.user))
        self.assertTrue(self.photo.is_allowed_for_user(self.other))

    def test_public_photo_no_inherit(self):
        AlbumAccessPolicy.objects.create(album=self.album, inherit=False, public=True)
        self.assertFalse(self.photo.is_allowed_for_user(self.user))
        PhotoAccessPolicy.objects.create(photo=self.photo, public=True)
        self.assertTrue(self.photo.is_allowed_for_user(self.user))

    def test_user_photo_no_inherit(self):
        policy = AlbumAccessPolicy.objects.create(album=self.album, inherit=False, public=False)
        policy.users.add(self.user)
        self.assertFalse(self.photo.is_allowed_for_user(self.user))
        self.assertFalse(self.photo.is_allowed_for_user(self.other))
        policy = PhotoAccessPolicy.objects.create(photo=self.photo, public=False)
        policy.users.add(self.user)
        self.assertTrue(self.photo.is_allowed_for_user(self.user))
        self.assertFalse(self.photo.is_allowed_for_user(self.other))

    def test_group_photo_no_inherit(self):
        policy = AlbumAccessPolicy.objects.create(album=self.album, inherit=False, public=False)
        policy.groups.add(self.group)
        self.assertFalse(self.photo.is_allowed_for_user(self.user))
        self.assertFalse(self.photo.is_allowed_for_user(self.other))
        policy = PhotoAccessPolicy.objects.create(photo=self.photo, public=False)
        policy.groups.add(self.group)
        self.assertTrue(self.photo.is_allowed_for_user(self.user))
        self.assertFalse(self.photo.is_allowed_for_user(self.other))

    def test_user_group_photo_no_inherit(self):
        policy = AlbumAccessPolicy.objects.create(album=self.album, inherit=False, public=False)
        policy.groups.add(self.group)
        policy.users.add(self.other)
        self.assertFalse(self.photo.is_allowed_for_user(self.user))
        self.assertFalse(self.photo.is_allowed_for_user(self.other))
        policy = PhotoAccessPolicy.objects.create(photo=self.photo, public=False)
        policy.groups.add(self.group)
        policy.users.add(self.other)
        self.assertTrue(self.photo.is_allowed_for_user(self.user))
        self.assertTrue(self.photo.is_allowed_for_user(self.other))

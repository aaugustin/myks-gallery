# coding: utf-8
# Copyright (c) 2011-2012 Aymeric Augustin. All rights reserved.

import datetime
import os
import shutil
import tempfile

from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from ..models import Album, AlbumAccessPolicy, Photo, PhotoAccessPolicy


class AdminTests(TestCase):

    def setUp(self):
        self.album = Album.objects.create(category='default', dirpath='foo', date=datetime.date.today())
        self.album2 = Album.objects.create(category='default', dirpath='foo2', date=datetime.date.today())
        AlbumAccessPolicy.objects.create(album=self.album, public=True, inherit=False)
        self.photo = Photo.objects.create(album=self.album, filename='bar')
        self.photo2 = Photo.objects.create(album=self.album, filename='bar2')
        PhotoAccessPolicy.objects.create(photo=self.photo, public=True)
        self.user = User.objects.create_superuser('user', 'user@gallery', 'pass')
        self.client.login(username='user', password='pass')

    def test_album_changelist(self):
        self.client.get(reverse('admin:gallery_album_changelist'))

    def test_photo_changelist(self):
        self.client.get(reverse('admin:gallery_photo_changelist'))

    def test_album_change(self):
        self.client.get(reverse('admin:gallery_album_change', args=[self.album.pk]))

    def test_photo_change(self):
        self.client.get(reverse('admin:gallery_photo_change', args=[self.photo.pk]))

    def test_scan_photos(self):
        self.client.get(reverse('admin:gallery.admin.scan_photos'))
        tmpdir = tempfile.mkdtemp()
        with open(os.path.join(tmpdir, 'test'), 'wb') as handle:
            handle.write('test')
        try:
            with override_settings(GALLERY_PHOTO_DIR=tmpdir):
                self.client.post(reverse('admin:gallery.admin.scan_photos'))
        finally:
            shutil.rmtree(tmpdir)

    def test_set_album_access_policy(self):
        response = self.client.post(reverse('admin:gallery_album_changelist'), {
            'action': 'set_access_policy',
            ACTION_CHECKBOX_NAME: [str(self.album.pk), str(self.album2.pk)],
        })
        self.assertTemplateUsed(response, 'admin/gallery/set_access_policy.html')
        self.assertFalse(Album.objects.get(pk=self.album.pk).access_policy.inherit)
        with self.assertRaises(AlbumAccessPolicy.DoesNotExist):
            Album.objects.get(pk=self.album2.pk).access_policy

        response = self.client.post(reverse('admin:gallery_album_changelist'), {
            'action': 'set_access_policy',
            ACTION_CHECKBOX_NAME: [str(self.album.pk), str(self.album2.pk)],
            'public': True,
            'inherit': True,
            'set_access_policy': "Set access policy",
        })
        self.assertRedirects(response, reverse('admin:gallery_album_changelist'))
        self.assertTrue(Album.objects.get(pk=self.album.pk).access_policy.inherit)
        self.assertTrue(Album.objects.get(pk=self.album2.pk).access_policy.inherit)

    def test_unset_album_access_policy(self):
        response = self.client.post(reverse('admin:gallery_album_changelist'), {
            'action': 'unset_access_policy',
            ACTION_CHECKBOX_NAME: [str(self.album.pk), str(self.album2.pk)],
        })
        self.assertTemplateUsed(response, 'admin/gallery/unset_access_policy.html')
        self.assertTrue(Album.objects.get(pk=self.album.pk).access_policy.public)

        response = self.client.post(reverse('admin:gallery_album_changelist'), {
            'action': 'unset_access_policy',
            ACTION_CHECKBOX_NAME: [str(self.album.pk), str(self.album2.pk)],
            'public': True,
            'unset_access_policy': "Unset access policy",
        })
        self.assertRedirects(response, reverse('admin:gallery_album_changelist'))
        with self.assertRaises(AlbumAccessPolicy.DoesNotExist):
            Album.objects.get(pk=self.album.pk).access_policy

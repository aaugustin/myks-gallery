# coding: utf-8
# Copyright (c) 2011-2012 Aymeric Augustin. All rights reserved.

import datetime
import os
import shutil
import tempfile

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

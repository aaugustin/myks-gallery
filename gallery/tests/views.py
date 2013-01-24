# coding: utf-8
# Copyright (c) 2011-2012 Aymeric Augustin. All rights reserved.

import datetime
import os

from django.core.urlresolvers import reverse
from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.test.utils import override_settings

from ..models import Album, AlbumAccessPolicy, Photo


class ViewsTests(TestCase):

    def setUp(self):
        self.album = Album.objects.create(category='default', dirpath='foo', date=datetime.date.today())
        AlbumAccessPolicy.objects.create(album=self.album, public=True, inherit=True)
        self.photo = Photo.objects.create(album=self.album, filename='bar')

    def test_index_view(self):
        response = self.client.get(reverse('gallery:index'))
        self.assertTemplateUsed(response, 'gallery/album_archive.html')

    def test_year_view(self):
        response = self.client.get(reverse('gallery:year', args=[self.album.date.year]))
        self.assertTemplateUsed(response, 'gallery/album_archive_year.html')

    def test_album_view(self):
        response = self.client.get(reverse('gallery:album', args=[self.album.pk]))
        self.assertTemplateUsed(response, 'gallery/album_detail.html')

    def test_photo_view(self):
        response = self.client.get(reverse('gallery:photo', args=[self.photo.pk]))
        self.assertTemplateUsed(response, 'gallery/photo_detail.html')

    def test_latest_view(self):
        response = self.client.get(reverse('gallery:latest'))
        self.assertRedirects(response, reverse('gallery:album', args=[self.album.pk]))


class ViewsWithPermissionTests(ViewsTests):

    def setUp(self):
        self.album = Album.objects.create(category='default', dirpath='foo', date=datetime.date.today())
        self.photo = Photo.objects.create(album=self.album, filename='bar')
        self.user = User.objects.create_user('user', 'user@gallery', 'pass')
        self.user.user_permissions.add(Permission.objects.get(codename='view'))
        self.client.login(username='user', password='pass')


class ServePrivateMediaTests(TestCase):

    # Constants used by the tests

    root_dir = os.path.dirname(os.path.dirname(__file__))
    relative_path = os.sep + os.path.join('static', 'css', 'gallery.css')
    absolute_path = root_dir + relative_path
    with open(absolute_path) as handle:
        file_contents = handle.read()
    private_url = '/private' + absolute_path

    # Without sendfile

    @override_settings(DEBUG=True)
    def test_no_sendfile_dev(self):
        response = self.client.get(self.private_url)
        self.assertEqual(response.get(''), None)
        self.assertEqual(''.join(response.streaming_content), self.file_contents)

    @override_settings(DEBUG=False)
    def test_no_sendfile_prod(self):
        response = self.client.get(self.private_url)
        self.assertEqual(response.get(''), None)
        self.assertEqual(''.join(response.streaming_content), self.file_contents)

    # See https://tn123.org/mod_xsendfile/

    @override_settings(DEBUG=True, GALLERY_SENDFILE_HEADER='X-SendFile', GALLERY_SENDFILE_ROOT='')
    def test_apache_dev(self):
        response = self.client.get(self.private_url)
        self.assertEqual(response.get('X-SendFile'), None)
        self.assertEqual(response.content, self.file_contents)

    @override_settings(DEBUG=False, GALLERY_SENDFILE_HEADER='X-SendFile', GALLERY_SENDFILE_ROOT='')
    def test_apache_prod(self):
        response = self.client.get(self.private_url)
        self.assertEqual(response.get('X-SendFile'), self.absolute_path)
        self.assertEqual(response.content, '')

    # See http://wiki.nginx.org/XSendfile

    @override_settings(DEBUG=True, GALLERY_SENDFILE_HEADER='X-Accel-Redirect', GALLERY_SENDFILE_ROOT=root_dir)
    def test_nginx_dev(self):
        response = self.client.get(self.private_url)
        self.assertEqual(response.get('X-Accel-Redirect'), None)
        self.assertEqual(response.content, self.file_contents)

    @override_settings(DEBUG=False, GALLERY_SENDFILE_HEADER='X-Accel-Redirect', GALLERY_SENDFILE_ROOT=root_dir)
    def test_nginx_prod(self):
        response = self.client.get(self.private_url)
        self.assertEqual(response.get('X-Accel-Redirect'), self.relative_path)
        self.assertEqual(response.content, '')

    # Other tests

    @override_settings(DEBUG=True)      # don't depend on a 404 template
    def test_no_such_file(self):
        response = self.client.get(self.private_url + '.does.not.exist')
        self.assertEqual(response.status_code, 404)

    @override_settings(DEBUG=False, GALLERY_SENDFILE_HEADER='X-Accel-Redirect', GALLERY_SENDFILE_ROOT=root_dir + root_dir)
    def test_file_not_under_root(self):
        self.assertRaises(ValueError, self.client.get, self.private_url)

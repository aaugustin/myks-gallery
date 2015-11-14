# coding: utf-8

from __future__ import unicode_literals

import datetime
import os
import shutil
import tempfile
import zipfile

from django.contrib.auth.models import Permission, User
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from .models import Album, AlbumAccessPolicy, Photo
from .storages import get_storage
from .test_imgutil import make_image


class ViewsTestsMixin(object):

    def setUp(self):
        super(ViewsTestsMixin, self).setUp()
        self.tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmpdir)
        self.storage = FileSystemStorage(location=self.tmpdir)

    def make_image(self):
        make_image(get_storage('photo'), self.photo.image_name(), 48, 36)

    def test_index_view(self):
        response = self.client.get(reverse('gallery:index'))
        self.assertTemplateUsed(response, 'gallery/album_archive.html')

    def test_search_view(self):
        response = self.client.get(reverse('gallery:index'), {'q': 'original'})
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

    def test_album_export_view(self):
        with self.settings(
                GALLERY_PHOTO_DIR=self.tmpdir,
                GALLERY_CACHE_DIR=self.tmpdir,
                GALLERY_SENDFILE_HEADER='X-Fake-Sendfile'):
            self.make_image()
            url = reverse('gallery:album-export', args=[self.album.pk])
            response = self.client.get(url)
            self.assertTrue(response['X-Fake-Sendfile'].startswith(self.tmpdir))
            with zipfile.ZipFile(response['X-Fake-Sendfile']) as archive:
                self.assertEqual(archive.namelist(), ['original.jpg'])

    def test_photo_resized_view_local(self):
        with self.settings(
                GALLERY_PHOTO_DIR=self.tmpdir,
                GALLERY_CACHE_DIR=self.tmpdir,
                GALLERY_RESIZE_PRESETS={'resized': (120, 120, False)},
                GALLERY_SENDFILE_HEADER='X-Fake-Sendfile'):
            self.make_image()
            url = reverse('gallery:photo-resized', args=['resized', self.photo.pk])
            response = self.client.get(url)
            self.assertTrue(response['X-Fake-Sendfile'].startswith(self.tmpdir))
            self.assertNotEqual(response['X-Fake-Sendfile'],
                                os.path.join(self.tmpdir, 'original.jpg'))

    def test_photo_resized_view_remote(self):
        with self.settings(
                GALLERY_CACHE_STORAGE='gallery.test_storages.RemoteStorage',
                GALLERY_PHOTO_STORAGE='gallery.test_storages.RemoteStorage',
                GALLERY_RESIZE_PRESETS={'resized': (120, 120, False)}):
            self.make_image()
            url = reverse('gallery:photo-resized', args=['resized', self.photo.pk])
            response = self.client.get(url)
            self.assertRedirects(response, '/url/of/' + self.photo.thumb_name('resized'),
                                 fetch_redirect_response=False)

    def test_photo_original_view_local(self):
        with self.settings(
                GALLERY_PHOTO_DIR=self.tmpdir,
                GALLERY_SENDFILE_HEADER='X-Fake-Sendfile'):
            self.make_image()
            url = reverse('gallery:photo-original', args=[self.photo.pk])
            response = self.client.get(url)
            self.assertEqual(response['X-Fake-Sendfile'],
                             os.path.join(self.tmpdir, 'original.jpg'))

    def test_photo_original_view_remote(self):
        with self.settings(
                GALLERY_PHOTO_STORAGE='gallery.test_storages.RemoteStorage'):
            self.make_image()
            url = reverse('gallery:photo-original', args=[self.photo.pk])
            response = self.client.get(url)
            self.assertRedirects(response, '/url/of/' + self.photo.image_name(),
                                 fetch_redirect_response=False)

    def test_latest_view(self):
        response = self.client.get(reverse('gallery:latest'))
        self.assertRedirects(response, reverse('gallery:album', args=[self.album.pk]))
        self.album.delete()
        response = self.client.get(reverse('gallery:latest'))
        self.assertRedirects(response, reverse('gallery:index'))


class ViewsWithPermissionTests(ViewsTestsMixin, TestCase):

    def setUp(self):
        super(ViewsWithPermissionTests, self).setUp()
        today = datetime.date.today()
        self.album = Album.objects.create(category='default', dirpath=self.tmpdir, date=today)
        self.photo = Photo.objects.create(album=self.album, filename='original.jpg')
        self.user = User.objects.create_user('user', 'user@gallery', 'pass')
        self.user.user_permissions.add(Permission.objects.get(codename='view'))
        self.client.login(username='user', password='pass')


class ViewsWithPrivateAccessPolicyTests(ViewsTestsMixin, TestCase):

    def setUp(self):
        super(ViewsWithPrivateAccessPolicyTests, self).setUp()
        today = datetime.date.today()
        self.album = Album.objects.create(category='default', dirpath=self.tmpdir, date=today)
        AlbumAccessPolicy.objects.create(album=self.album, public=False, inherit=True)
        self.photo = Photo.objects.create(album=self.album, filename='original.jpg')
        self.user = User.objects.create_user('user', 'user@gallery', 'pass')
        self.album.access_policy.users.add(self.user)
        self.client.login(username='user', password='pass')

    def test_hide_private_albums(self):
        self.client.logout()
        response = self.client.get(reverse('gallery:index'))
        self.assertQuerysetEqual(response.context['latest'], [])


class ViewsWithPublicAccessPolicyTests(ViewsTestsMixin, TestCase):

    def setUp(self):
        super(ViewsWithPublicAccessPolicyTests, self).setUp()
        today = datetime.date.today()
        self.album = Album.objects.create(category='default', dirpath=self.tmpdir, date=today)
        AlbumAccessPolicy.objects.create(album=self.album, public=True, inherit=True),
        self.photo = Photo.objects.create(album=self.album, filename='original.jpg')

    def test_show_and_hide_public_albums(self):
        # Public albums are shown for anonymous users
        response = self.client.get(reverse('gallery:index'))
        self.assertQuerysetEqual(response.context['latest'], [self.album], transform=lambda a: a)

        # By default public albums are hidden for authenticated users
        self.user = User.objects.create_user('user', 'user@gallery', 'pass')
        self.client.login(username='user', password='pass')
        response = self.client.get(reverse('gallery:index'))
        self.assertQuerysetEqual(response.context['latest'], [])

        # Showing public albums is persistent
        response = self.client.get(reverse('gallery:index') + '?show_public')
        self.assertQuerysetEqual(response.context['latest'], [self.album], transform=lambda a: a)
        response = self.client.get(reverse('gallery:index'))
        self.assertQuerysetEqual(response.context['latest'], [self.album], transform=lambda a: a)

        # Hiding public albums is persistent
        response = self.client.get(reverse('gallery:index') + '?hide_public')
        self.assertQuerysetEqual(response.context['latest'], [])
        response = self.client.get(reverse('gallery:index'))
        self.assertQuerysetEqual(response.context['latest'], [])


class ServePrivateMediaTests(TestCase):

    # Constants used by the tests

    root_dir = os.path.dirname(__file__)
    relative_path = os.sep + os.path.join('static', 'css', 'gallery.css')
    absolute_path = root_dir + relative_path
    with open(absolute_path, 'rb') as handle:
        file_contents = handle.read()
    private_url = '/private' + absolute_path

    # Without sendfile

    @override_settings(DEBUG=True)
    def test_no_sendfile_dev(self):
        response = self.client.get(self.private_url)
        self.assertEqual(response.get(''), None)
        self.assertEqual(b''.join(response.streaming_content), self.file_contents)

    @override_settings(DEBUG=False)
    def test_no_sendfile_prod(self):
        response = self.client.get(self.private_url)
        self.assertEqual(response.get(''), None)
        self.assertEqual(b''.join(response.streaming_content), self.file_contents)

    # See https://tn123.org/mod_xsendfile/

    @override_settings(
        DEBUG=True,
        GALLERY_SENDFILE_HEADER='X-SendFile',
        GALLERY_SENDFILE_ROOT='')
    def test_apache_dev(self):
        response = self.client.get(self.private_url)
        self.assertEqual(response.get('X-SendFile'), None)
        self.assertEqual(b''.join(response.streaming_content), self.file_contents)

    @override_settings(
        DEBUG=False,
        GALLERY_SENDFILE_HEADER='X-SendFile',
        GALLERY_SENDFILE_ROOT='')
    def test_apache_prod(self):
        response = self.client.get(self.private_url)
        self.assertEqual(response.get('X-SendFile'), self.absolute_path)
        self.assertEqual(response.content, b'')

    # See http://wiki.nginx.org/XSendfile

    @override_settings(
        DEBUG=True,
        GALLERY_SENDFILE_HEADER='X-Accel-Redirect',
        GALLERY_SENDFILE_ROOT=root_dir)
    def test_nginx_dev(self):
        response = self.client.get(self.private_url)
        self.assertEqual(response.get('X-Accel-Redirect'), None)
        self.assertEqual(b''.join(response.streaming_content), self.file_contents)

    @override_settings(
        DEBUG=False,
        GALLERY_SENDFILE_HEADER='X-Accel-Redirect',
        GALLERY_SENDFILE_ROOT=root_dir)
    def test_nginx_prod(self):
        response = self.client.get(self.private_url)
        self.assertEqual(response.get('X-Accel-Redirect'), self.relative_path)
        self.assertEqual(response.content, b'')

    # Other tests

    @override_settings(DEBUG=True)      # don't depend on a 404 template
    def test_no_such_file(self):
        response = self.client.get(self.private_url + '.does.not.exist')
        self.assertEqual(response.status_code, 404)

    @override_settings(
        DEBUG=False,
        GALLERY_SENDFILE_HEADER='X-Accel-Redirect',
        GALLERY_SENDFILE_ROOT=root_dir + root_dir)
    def test_file_not_under_root(self):
        self.assertRaises(ValueError, self.client.get, self.private_url)

# coding: utf-8

from __future__ import unicode_literals

import datetime
import os
import shutil
import sys
import tempfile
import unittest

from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth.models import Permission, User
from django.core.urlresolvers import reverse
from django.test import TestCase

from .models import Album, AlbumAccessPolicy, Photo, PhotoAccessPolicy


class AdminTests(TestCase):

    def setUp(self):
        today = datetime.date.today()
        self.album = Album.objects.create(category='default', dirpath='foo', date=today)
        self.album2 = Album.objects.create(category='default', dirpath='foo2', date=today)
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
        self.client.get(reverse('admin:gallery_scan_photos'))
        tmpdir = tempfile.mkdtemp()
        with open(os.path.join(tmpdir, 'test'), 'wb') as handle:
            handle.write(b'test')
        try:
            with self.settings(GALLERY_PHOTO_DIR=tmpdir):
                self.client.post(reverse('admin:gallery_scan_photos'))
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

    def test_set_album_access_policy_invalid_form(self):
        response = self.client.post(reverse('admin:gallery_album_changelist'), {
            'action': 'set_access_policy',
            ACTION_CHECKBOX_NAME: [str(self.album.pk), str(self.album2.pk)],
            'set_access_policy': "Set access policy",
            'users': ['-1'],
        })
        self.assertTemplateUsed(response, 'admin/gallery/set_access_policy.html')
        self.assertFormError(response, 'form', 'users',
                             'Select a valid choice. -1 is not one of the available choices.')

    def test_set_album_access_policy_no_add_permission(self):
        self.user.is_superuser = False
        self.user.save()
        self.user.user_permissions.add(Permission.objects.get(codename='change_album'))

        response = self.client.post(reverse('admin:gallery_album_changelist'), {
            'action': 'set_access_policy',
            ACTION_CHECKBOX_NAME: [str(self.album2.pk)],
            'public': True,
            'inherit': True,
            'set_access_policy': "Set access policy",
        })
        self.assertEqual(response.status_code, 403)
        with self.assertRaises(AlbumAccessPolicy.DoesNotExist):
            Album.objects.get(pk=self.album2.pk).access_policy

    def test_set_album_access_policy_add_permission(self):
        self.user.is_superuser = False
        self.user.save()
        self.user.user_permissions.add(Permission.objects.get(codename='change_album'))
        self.user.user_permissions.add(Permission.objects.get(codename='add_albumaccesspolicy'))

        response = self.client.post(reverse('admin:gallery_album_changelist'), {
            'action': 'set_access_policy',
            ACTION_CHECKBOX_NAME: [str(self.album2.pk)],
            'public': True,
            'inherit': True,
            'set_access_policy': "Set access policy",
        })
        self.assertRedirects(response, reverse('admin:gallery_album_changelist'))
        self.assertTrue(Album.objects.get(pk=self.album2.pk).access_policy.inherit)

    def test_set_album_access_policy_no_change_permission(self):
        self.user.is_superuser = False
        self.user.save()
        self.user.user_permissions.add(Permission.objects.get(codename='change_album'))

        response = self.client.post(reverse('admin:gallery_album_changelist'), {
            'action': 'set_access_policy',
            ACTION_CHECKBOX_NAME: [str(self.album.pk)],
            'public': True,
            'inherit': True,
            'set_access_policy': "Set access policy",
        })
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Album.objects.get(pk=self.album.pk).access_policy.inherit)

    def test_set_album_access_policy_change_permission(self):
        self.user.is_superuser = False
        self.user.save()
        self.user.user_permissions.add(Permission.objects.get(codename='change_album'))
        self.user.user_permissions.add(Permission.objects.get(codename='change_albumaccesspolicy'))

        response = self.client.post(reverse('admin:gallery_album_changelist'), {
            'action': 'set_access_policy',
            ACTION_CHECKBOX_NAME: [str(self.album.pk)],
            'public': True,
            'inherit': True,
            'set_access_policy': "Set access policy",
        })
        self.assertRedirects(response, reverse('admin:gallery_album_changelist'))
        self.assertTrue(Album.objects.get(pk=self.album.pk).access_policy.inherit)

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

    def test_unset_album_access_policy_no_delete_permission(self):
        self.user.is_superuser = False
        self.user.save()
        self.user.user_permissions.add(Permission.objects.get(codename='change_album'))

        response = self.client.post(reverse('admin:gallery_album_changelist'), {
            'action': 'unset_access_policy',
            ACTION_CHECKBOX_NAME: [str(self.album.pk)],
            'public': True,
            'unset_access_policy': "Unset access policy",
        })
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Album.objects.get(pk=self.album.pk).access_policy.public)

    def test_unset_album_access_policy_delete_permission(self):
        self.user.is_superuser = False
        self.user.save()
        self.user.user_permissions.add(Permission.objects.get(codename='change_album'))
        self.user.user_permissions.add(Permission.objects.get(codename='delete_albumaccesspolicy'))

        response = self.client.post(reverse('admin:gallery_album_changelist'), {
            'action': 'unset_access_policy',
            ACTION_CHECKBOX_NAME: [str(self.album.pk)],
            'public': True,
            'unset_access_policy': "Unset access policy",
        })
        self.assertRedirects(response, reverse('admin:gallery_album_changelist'))
        with self.assertRaises(AlbumAccessPolicy.DoesNotExist):
            Album.objects.get(pk=self.album.pk).access_policy

    # See https://code.djangoproject.com/ticket/24258
    if (3, 0) <= sys.version_info[:2] < (3, 3):             # pragma: no cover
        test_set_album_access_policy = unittest.expectedFailure(test_set_album_access_policy)
        test_set_album_access_policy_add_permission = unittest.expectedFailure(test_set_album_access_policy_add_permission)  # noqa
        test_set_album_access_policy_change_permission = unittest.expectedFailure(test_set_album_access_policy_change_permission)  # noqa
        test_unset_album_access_policy = unittest.expectedFailure(test_unset_album_access_policy)
        test_unset_album_access_policy_delete_permission = unittest.expectedFailure(test_unset_album_access_policy_delete_permission)  # noqa

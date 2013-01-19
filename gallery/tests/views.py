# coding: utf-8
# Copyright (c) 2011-2012 Aymeric Augustin. All rights reserved.

import os

from django.test import TestCase
from django.test.utils import override_settings


class ServePrivateMediaTests(TestCase):
    urls = 'gallery.tests.urls'

    # Constants used by the tests

    root_dir = os.path.dirname(os.path.dirname(__file__))
    relative_path = os.sep + os.path.join('static', 'css', 'gallery.css')
    absolute_path = root_dir + relative_path
    with open(absolute_path) as handle:
        file_contents = handle.read()
    private_url = '/private' + absolute_path

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

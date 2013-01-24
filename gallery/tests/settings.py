from __future__ import unicode_literals

import os

# Django settings

DATABASES = {
    'default': {'ENGINE': 'django.db.backends.sqlite3'},
}

INSTALLED_APPS = (
    'gallery',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
)

ROOT_URLCONF = 'gallery.tests.urls'

SECRET_KEY = 'Not empty for tests.'

STATIC_URL = '/static/'

TEMPLATE_DIRS = os.path.join(os.path.dirname(__file__), 'templates'),

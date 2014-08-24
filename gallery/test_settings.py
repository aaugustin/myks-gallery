from __future__ import unicode_literals

import os

DATABASES = {
    'default': {'ENGINE': 'django.db.backends.sqlite3'},
}

INSTALLED_APPS = [
    'gallery',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
]

MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gallery.test_urls'

SECRET_KEY = 'Not empty for tests.'

STATIC_ROOT = '.'

STATIC_URL = '/static/'

TEMPLATE_DIRS = os.path.join(os.path.dirname(__file__), 'test_templates'),

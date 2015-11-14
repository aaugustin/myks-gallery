from __future__ import unicode_literals

import os

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))

# Django settings for example project.

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}

INSTALLED_APPS = (
    'example',
    'gallery.apps.GalleryConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
)

ROOT_URLCONF = 'example.urls'

SECRET_KEY = "don't run in production with a secret key committed to GitHub"

SITE_ID = 1

STATIC_URL = '/static/'

USE_I18N = True

USE_L10N = True

USE_TZ = True

WSGI_APPLICATION = 'example.wsgi.application'

# Gallery settings

GALLERY_PHOTO_STORAGE = 'example.storages.photo'

GALLERY_CACHE_STORAGE = 'example.storages.cache'

GALLERY_PATTERNS = (
    ('Photos', r'(?P<a_year>\d{4})_(?P<a_month>\d{2})_(?P<a_day>\d{2})_'
               r'(?P<a_name>[^/]+)/[^/]+.(jpg|JPG)'),
)

GALLERY_RESIZE_PRESETS = {
    'thumb': (128, 128, True),
    'standard': (768, 768, False),
}

GALLERY_RESIZE_OPTIONS = {
    'JPEG': {'quality': 95, 'optimize': True},
}

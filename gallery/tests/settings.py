from __future__ import unicode_literals

# Django settings

DATABASES = {
    'default': {'ENGINE': 'django.db.backends.sqlite3'},
}

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'gallery',
)

LOGGING_CONFIG = None

ROOT_URLCONF = 'gallery.tests.urls'

SECRET_KEY = 'Not empty for tests.'

# Custom settings

GALLERY_CACHE_DIR = ''

GALLERY_RESIZE_OPTIONS = {}

GALLERY_RESIZE_PRESETS = {}

GALLERY_PHOTO_DIR = ''

GALLERY_SENDFILE_HEADER = 'X-SendFile'

GALLERY_SENDFILE_ROOT = ''

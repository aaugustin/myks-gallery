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

PHOTO_CACHE = ''

PHOTO_IGNORES = ()

PHOTO_PATTERNS = ()

PHOTO_RESIZE_OPTIONS = {}

PHOTO_RESIZE_PRESETS = {}

PHOTO_ROOT = ''

SENDFILE_HEADER = 'X-SendFile'

SENDFILE_ROOT = ''

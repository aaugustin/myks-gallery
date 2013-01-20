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
    'gallery',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
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

GALLERY_PHOTO_DIR = os.path.join(ROOT_DIR, 'photos')

GALLERY_CACHE_DIR = os.path.join(ROOT_DIR, 'cache')

GALLERY_PATTERNS = (
    ('Photos', ur'(?P<a_year>\d{4})_(?P<a_month>\d{2})_(?P<a_day>\d{2})_(?P<a_name>[^/]+)/[^/]+.(jpg|JPG)'),
)

GALLERY_RESIZE_PRESETS = {
    'thumb': (128, 128, True),
    'standard': (768, 768, False),
}

GALLERY_RESIZE_OPTIONS = {
    'JPEG': {'quality': 95, 'optimize': True},
}

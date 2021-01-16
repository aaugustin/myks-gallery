from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Django settings

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DEBUG = True

INSTALLED_APPS = [
    'example',
    'gallery.apps.GalleryConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'example.urls'

SECRET_KEY = "don't run in production with a secret key committed to GitHub"

STATIC_URL = '/static/'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

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

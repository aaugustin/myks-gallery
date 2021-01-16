from django.conf import settings
from django.core.files.storage import FileSystemStorage


def photo():
    return FileSystemStorage(location=settings.BASE_DIR / 'photos')


def cache():
    return FileSystemStorage(location=settings.BASE_DIR / 'cache')

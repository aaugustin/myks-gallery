from django.conf import settings
from django.core.files.storage import FileSystemStorage


def photo():
    return FileSystemStorage(
        location=settings.MEDIA_ROOT / "photos",
        base_url=settings.MEDIA_URL + "photos/",
    )


def cache():
    return FileSystemStorage(
        location=settings.MEDIA_ROOT / "cache",
        base_url=settings.MEDIA_URL + "cache/",
    )

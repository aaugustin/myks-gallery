import functools

from django.conf import settings
from django.dispatch import receiver
from django.test.signals import setting_changed
from django.utils.module_loading import import_string


@functools.lru_cache()
def get_resize():
    resize = getattr(settings, "GALLERY_RESIZE", "gallery.resizers.pillow.resize")
    return import_string(resize)


@receiver(setting_changed)
def clear_get_resize_cache(**kwargs):
    if kwargs["setting"] == "GALLERY_RESIZE":
        get_resize.cache_clear()

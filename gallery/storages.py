import functools
import re

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.dispatch import receiver
from django.test.signals import setting_changed
from django.utils.module_loading import import_string


@functools.lru_cache()
def get_storage(name):
    storage_setting = f"GALLERY_{name.upper()}_STORAGE"
    try:
        storage = getattr(settings, storage_setting)
    except AttributeError:
        raise ImproperlyConfigured(f"Please define {storage_setting}")
    if isinstance(storage, str):
        return import_string(storage)()
    else:
        # To make testing ealier, the setting can be set to the storage itself.
        return storage


@receiver(setting_changed)
def clear_get_storage_cache(**kwargs):
    if re.match(r"^GALLERY_[A-Z]+_STORAGE$", kwargs["setting"]):
        get_storage.cache_clear()

# coding: utf-8

from __future__ import unicode_literals

import re

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage
from django.dispatch import receiver
from django.test.signals import setting_changed
from django.utils.lru_cache import lru_cache
from django.utils.module_loading import import_string


@lru_cache()
def get_storage(name):
    name = name.upper()
    storage_setting = 'GALLERY_{}_STORAGE'.format(name)
    dir_setting = 'GALLERY_{}_DIR'.format(name)
    try:
        storage_class = getattr(settings, storage_setting)
    except AttributeError:
        # There's a good chance that this fallback will survive for a long
        # time because deprecating it would require updating all the tests.
        try:
            storage_dir = getattr(settings, dir_setting)
        except AttributeError:
            raise ImproperlyConfigured(
                "Please define {} or {}".format(storage_setting, dir_setting))
        else:
            return FileSystemStorage(location=storage_dir)
    else:
        return import_string(storage_class)()


@receiver(setting_changed)
def clear_storages_cache(**kwargs):
    if re.match(r'^GALLERY_[A-Z]+_(STORAGE|DIR)$', kwargs['setting']):
        get_storage.cache_clear()

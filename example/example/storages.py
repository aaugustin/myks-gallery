# coding: utf-8

from __future__ import unicode_literals

import os.path

from django.core.files.storage import FileSystemStorage

from .settings import ROOT_DIR


def photo():
    return FileSystemStorage(location=os.path.join(ROOT_DIR, 'photos'))


def cache():
    return FileSystemStorage(location=os.path.join(ROOT_DIR, 'cache'))

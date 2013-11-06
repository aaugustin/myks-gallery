# coding: utf-8
# Copyright (c) 2011-2012 Aymeric Augustin. All rights reserved.

from __future__ import unicode_literals

import django

if django.VERSION[:2] < (1, 6):     # unittest-style discovery isn't available
    from .test_admin import *
    from .test_imgutil import *
    from .test_models import *
    from .test_views import *

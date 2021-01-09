from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class GalleryConfig(AppConfig):
    name = 'gallery'
    verbose_name = _("Gallery")

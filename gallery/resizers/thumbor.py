# Resize images with Thumbor

# The implementation assumes that Thumbor is configured to access photos
# directly. See https://github.com/aaugustin/myks-thumbor for an example.

# It requires THUMBOR_SERVER and THUMBOR_SECURITY_KEY settings.

import urllib.parse

import libthumbor
from django.conf import settings


def resize(photo, width, height, crop=True):
    image_url = urllib.parse.quote(
        photo.image_name.encode(),
        safe="~@#$&()*!+=:;,.?/'",
    )
    url = libthumbor.CryptoURL(key=settings.THUMBOR_SECURITY_KEY).generate(
        image_url=image_url,
        width=width,
        height=height,
        fit_in=not crop,
        smart=True,
    )
    return settings.THUMBOR_SERVER + urllib.parse.unquote(url)

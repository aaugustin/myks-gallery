mYk's gallery
#############

Goals
=====

myks-gallery is an simple photo gallery with granular access control.

It's designed for my personal needs:

- access my entire photo collection privately,
- share some albums with family or friends,
- make some albums public.

It powers my `humble photo gallery`_.

It's a pluggable Django application.

.. _humble photo gallery: http://myks.org/photos/

Usage
=====

I don't use a photo manager; I just create a new directory for each event and
put my photos inside. I include the date of the event in the name of the
directory and I rename photos based on their EXIF date and time. I regularly
synchronize my collection to a server with rsync_. I use myks-gallery as web
frontend to share them and to view them when I'm not at home.

.. _rsync: http://rsync.samba.org/

Whenever I upload new photos, I re-scan the collection with ``./manage.py
scanphotos``, and myks-gallery detects new albums and photos. There's a "Scan
photos" button in the admin that has exactly the same effect. Then I define
users, groups and access policies through the admin.

If you have a similar workflow, you may find myks-gallery useful.

Album access policies control the visibility of albums. Most often, you'll
enable the "photos inherit album access policy" option. If you need more
control, for instance to share only a subset of an album, you can disable this
option and use photo access policies. You still need to define an album access
policy, and it should be a superset of the photo access policies.

Obviously, requiring usernames and passwords doesn't work well for sharing
photos with relatives. You might want to use django-sesame_.

.. _django-sesame: https://github.com/aaugustin/django-sesame

Setup
=====

myks-gallery requires Python 2.6 or 2.7, Django 1.5 and PIL.

Installation guide
------------------

This application isn't exactly plug'n'play. There are many moving pieces.
Here's the general process for integrating it into a website.

1.  Download and install the package from PyPI::

        $ pip install myks-gallery

2.  Add ``gallery`` to ``INSTALLED_APPS``::

        INSTALLED_APPS += 'gallery',

3.  Configure the settings — see below for the list.

4.  Add the application to your URLconf with the ``gallery`` application
    namespace::

        urlpatterns += patterns('',
            url(r'^gallery/', include('gallery.urls', namespace='gallery', app_name='gallery')),
        )

5.  Create a suitable ``base.html`` template — see below for details.

6.  Enable `X-accel`_ (nginx) or `mod_xsendfile`_ (Apache) for your photo and
    cache directories (``GALLERY_PHOTO_DIR`` and ``GALLERY_CACHE_DIR``).

7.  Scan your photos with the "Scan photos" button in the admin or the
    ``scanphotos`` management command and define access policies.

.. _X-accel: http://wiki.nginx.org/X-accel
.. _mod_xsendfile: https://tn123.org/mod_xsendfile/

Settings
--------

``GALLERY_PHOTO_DIR``
.....................

Default: not defined

Path to the directory containing your photos. This directory must be readable
by the application server but should not be writable.

``GALLERY_CACHE_DIR``
.....................

Default: not defined

Path to the cache directory for thumbnails. This directory must be readable
and writable by the application server.

``GALLERY_PATTERNS``
....................

Default: not defined

Tuple of (category name, regular expression) defining how to extract album
information — category, date, name — from the paths of photo files.

The regular expressions match paths relative to ``GALLERY_PHOTO_DIR``. They
contain the following captures:

- ``a_name``: album name (mandatory) — to capture several bits, use
  ``a_name1``, ``a_name2``, etc.
- ``a_year``, ``a_month``, ``a_day``: album date (mandatory)
- ``p_year``, ``p_month``, ``p_day``, ``p_hour``, ``p_minute``, ``p_second``:
  photo date and time (optional)

Here's an example, for photos stored with names such as ``2013/01_19_Snow in
Paris/2013-01-19_19-12-43.jpg``::

    GALLERY_PATTERNS = (
        ('Photos',
            ur'(?P<a_year>\d{4})/(?P<a_month>\d{2})_(?P<a_day>\d{2})_'
            ur'(?P<a_name>[^_/]+)/'
            ur'(?P<p_year>\d{4})-(?P<p_month>\d{2})-(?P<p_day>\d{2})_'
            ur'(?P<p_hour>\d{2})-(?P<p_minute>\d{2})-(?P<p_second>\d{2})\.jpg'),
    )

``GALLERY_IGNORES``
...................

Default: ``()``

Tuple of regular expressions matching paths relative to ``GALLERY_PHOTO_DIR``.
Files matching one of these expressions will be ignored when scanning photos.

``GALLERY_RESIZE_PRESETS``
..........................

Default: not defined

Dictionary mapping thumbnail presets names to ``(width, height, crop)``. If
``crop`` is ``True``, the photo will be cropped and the thumbnail will have
exactly the requested size. If ``crop`` is ``False``, the thumbnaill will be
smaller than the requested size in one dimension to preserve the photo's
aspect ratio.

The default templates assume the following values::

    GALLERY_RESIZE_PRESETS = {
        'thumb': (256, 256, True),
        'standard': (1536, 1536, False),
    }

``GALLERY_RESIZE_OPTIONS``
..........................

Default: ``{}``

Dictionary mapping image formats names to to dictionaries of options for PIL's
``save`` method. Options are described for each file format in PIL's handbook.

This is a reasonable value::

    GALLERY_RESIZE_OPTIONS = {
        'JPEG': {'quality': 95, 'optimize': True, 'progressive': True},
    }

.. _options:

``GALLERY_SENDFILE_HEADER``
............................

Default: not defined

Name of the HTTP header that triggers ``sendfile`` on your web server. Use
``'X-Accel-Redirect'`` for nginx and ``'X-SendFile'`` for Apache.

``GALLERY_SENDFILE_ROOT``
.........................

Default: not defined

Part to strip at the beginning of the paths in the ``sendfile`` header. This
must be the absolute path to the root of the internal location for nginx. It
may be equal to the value of ``XSendFilePath`` or empty for Apache.

``GALLERY_TITLE``
.................

Default: ``"Gallery"``

Title of your photo gallery. This is only used by the default templates of the
index and year views.

Templates
---------

The default templates included in this application extend a template called
``base.html``. It is your responsibility to provide this template.

It must provide three blocks: ``title``, ``extrahead``, ``content``. Rather
than a long explanation, here is a short example::

    <!DOCTYPE html>
    <html>
        <head>
            <title>{% block title %}{% endblock %}</title>
            {% block extrahead %}{% endblock %}
        </head>
        <body>
            {% block content %}{% endblock %}
        </body>
    </html>

mYk's gallery
#############

Introduction
============

`myks-gallery`_ is a simple photo gallery with granular access control.

It powers my `humble photo gallery`_, allowing me to:

- access my entire photo collection privately,
- share some albums with family or friends,
- make some albums public.

.. _myks-gallery: https://github.com/aaugustin/myks-gallery
.. _humble photo gallery: https://myks.org/photos/

Use case
========

Rather than use a photo manager, I just create a new directory for each event
and put my photos inside. I include the date of the event in the name of the
directory and I rename photos based on their date and time. Then I regularly
synchronize my collection to a remote storage. I serve my gallery from there.

If you have a similar workflow, you may find myks-gallery useful.

Whenever I upload new photos, I re-scan the collection with ``django-admin
scanphotos`` or with the button in the admin. myks-gallery detects new albums
and photos. Then I define users, groups and access policies in the admin.

Album access policies control the visibility of albums. Most often, you'll
enable the "photos inherit album access policy" option. If you need more
control, for instance to share only a subset of an album, you can disable this
option and use photo access policies. You still need to define an album access
policy and it should be a superset of the photo access policies.

Obviously, requiring usernames and passwords doesn't work well for sharing
photos with relatives. You might want to use django-sesame_.

.. _django-sesame: https://github.com/aaugustin/django-sesame

Setup
=====

myks-gallery is a pluggable Django application. It requires:

* Django ≥ 3.2 (LTS)
* Python ≥ 3.6

Architecture
------------

myks-gallery requires two storage areas:

- The first one contains the original photos. It's a read-only reference. You
  can upload photos with `aws s3 sync`_, `gsutil rsync`_, etc.
- The second one contains resized versions and ZIP archives of album exports.
  It's a cache. You can set up expiry policies and clear it without affecting
  the gallery, aside from the cost of rescaling images again.

myks-gallery accesses them through Django's `file storage API`_, meaning that
you can use any storage for which a Django storage backend exists. You should
use a third-party storage backend if you're storing files in a cloud service.

.. _aws s3 sync: https://docs.aws.amazon.com/cli/latest/reference/s3/sync.html
.. _gsutil rsync: https://cloud.google.com/storage/docs/gsutil/commands/rsync
.. _file storage API: https://docs.djangoproject.com/en/stable/ref/files/storage/

Installation guide
------------------

This application isn't exactly plug'n'play. There are many moving pieces.
Here's the general process for integrating myks-gallery into an existing
website:

1.  Download and install the package from PyPI::

        $ pip install myks-gallery Pillow

2.  Add ``gallery.apps.GalleryConfig`` to ``INSTALLED_APPS``::

        INSTALLED_APPS += ['gallery.apps.GalleryConfig']

3.  Configure the settings — see below for the list.

4.  Add the application to your URLconf with the ``gallery`` application
    namespace::

        urlpatterns += [
            path('gallery/', include('gallery.urls', namespace='gallery')),
        ]

5.  Create a suitable ``base.html`` template. It must provide three blocks:
    ``title``, ``extrahead``, ``content``, as shown in this `example`_.

6.  Scan your photos with the "Scan photos" button in the admin or the
    ``scanphotos`` management command and define access policies.

The source_ contains a sample application in the ``example`` directory. It can
help you see how everything fits together. See below for how to run it.

.. _example: https://github.com/aaugustin/myks-gallery/blob/master/example/example/templates/base.html
.. _X-accel: http://wiki.nginx.org/X-accel
.. _mod_xsendfile: https://tn123.org/mod_xsendfile/
.. _source: https://github.com/aaugustin/myks-gallery

Access control
--------------

myks-gallery provides two levels of access control: by album and by photo.

By default, albums and photos aren't visible by anyone, except users with the
"Can see all photos" permission, including superusers who have it implicitly.

To make them visible, you must define an access policy. You have two options:
public access or access restricted to select users or groups.

Access policies for albums are configured explicitly in the admin.

In most cases, you will enable the "Photos inherit album access policy"
option, so that the access policy also applies to all photos in the album.

Access policies for photos may also be configured for granular control.

For example, if you want to publish just a few photos in an album, make these
photos public, make the album public, but don't enable "Photos inherit album
access policy". Other photos in the album won't be visible.

Another example, if you want to share an album privately except for a few
photos, set an empty access policy on these photos (e.g. by adding then
removing yourself), then allow some groups or users to view the album.

Permissions
-----------

myks-gallery defines two permissions for ``django.contrib.auth``:

- "Can scan the photos directory" allows using the "Scan photos" button in the
  admin.
- "Can see all photos" allows seeing all albums and all photos regardless of
  access policies.

Settings
--------

``GALLERY_PHOTO_STORAGE``
.........................

Default: *not defined*

Dotted Python path to the Django storage class for the original photos. It
must be readable by the application server but should not be writable.

While ``GALLERY_PHOTO_STORAGE`` behaves like Django's ``DEFAULT_FILE_STORAGE``
setting, you'll usullay point it to a factory function that initializes and
returns a Django storage instance because you won't want to use globally
configured values for settings such as the S3 bucket name.

``GALLERY_CACHE_STORAGE``
.........................

Default: *not defined*

Dotted Python path to the Django storage class for resized versions and album
archives. It must be readable and writable by the application server.

It behaves like ``GALLERY_PHOTO_STORAGE``.

``GALLERY_PATTERNS``
....................

Default: ``()``

Tuple of (category name, regular expression) defining how to extract album
information — category, date, name — from the paths of photo files.

The regular expressions match paths relative to the root of the photo storage.
They contain the following captures:

- ``a_name``: album name (mandatory) — to capture several bits, use
  ``a_name1``, ``a_name2``, etc.
- ``a_year``, ``a_month``, ``a_day``: album date (mandatory)
- ``p_year``, ``p_month``, ``p_day``, ``p_hour``, ``p_minute``, ``p_second``:
  photo date and time (optional)

Here's an example, for photos stored with names such as ``2013/01_19_Snow in
Paris/2013-01-19_19-12-43.jpg``::

    GALLERY_PATTERNS = (
        ('Photos',
            r'(?P<a_year>\d{4})/(?P<a_month>\d{2})_(?P<a_day>\d{2})_'
            r'(?P<a_name>[^_/]+)/'
            r'(?P<p_year>\d{4})-(?P<p_month>\d{2})-(?P<p_day>\d{2})_'
            r'(?P<p_hour>\d{2})-(?P<p_minute>\d{2})-(?P<p_second>\d{2})\.jpg'),
    )

``GALLERY_IGNORES``
...................

Default: ``()``

Tuple of regular expressions matching paths within ``GALLERY_PHOTO_STORAGE``.
Files matching one of these expressions will be ignored when scanning photos.

``GALLERY_RESIZE``
..................

Default: ``gallery.resizers.pillow.resize``

Dotted Python path to the callable providing resizing functionality.

``resize(photo, width, height, crop=True)`` receives an instance of the
``Photo`` model and returns a URL for the resized version. The original image is
found at ``photo.image_name`` in the photo storage.

The default implementation depends on ``Pillow``.

``GALLERY_RESIZE_PRESETS``
..........................

Default: ``{}``

Dictionary mapping resizing presets to ``(width, height, crop)`` tuples. If
``crop`` is ``True``, the photo will be cropped and the thumbnail will have
exactly the requested size. If ``crop`` is ``False``, the thumbnail will be
smaller than the requested size in one dimension to preserve the photo's
aspect ratio.

The default templates assume the following values::

    GALLERY_RESIZE_PRESETS = {
        'thumb': (128, 128, True),
        'standard': (768, 768, False),
    }

You may double these sizes for better results on high DPI displays.

The admin expects a ``'thumb'`` preset.

``GALLERY_RESIZE_OPTIONS``
..........................

Default: ``{}``

Dictionary mapping image formats names to dictionaries of options for Pillow's
``save`` method. Pillow's documentation describes options for each file format.

The following a reasonable value for high-quality thumbnails and previews::

    GALLERY_RESIZE_OPTIONS = {
        'JPEG': {'quality': 90, 'optimize': True},
    }

The default resizer honors this setting. Other resizers may ignore it.

``GALLERY_TITLE``
.................

Default: ``"Gallery"``

Title of your photo gallery. This is only used by the default templates of the
index and year views.

``GALLERY_PREVIEW_COUNT``
.........................

Default: ``5``

Number of thumbnails shown in the preview of each album.

Running the sample application
==============================

1.  Make sure Django and Pillow are installed.

2.  Create directories for storing photos and thumbnails::

        $ cd example
        $ mkdir media
        $ mkdir media/cache
        $ mkdir media/photos

3.  Create an album directory, whose name must contain a date, and download
    images. `Wikipedia's featured pictures`_ are a good choice::

        $ mkdir "media/photos/2023_01_01_Featured Pictures"
        # ... download pictures to this directory...

    .. _Wikipedia's featured pictures: https://en.wikipedia.org/wiki/Wikipedia:Featured_pictures

4.  Run the development server::

    $ ./manage.py migrate
    $ ./manage.py createsuperuser
    $ ./manage.py runserver

5.  Go to http://localhost:8000/admin/gallery/album/ and log in. Click the
    "Scan photos" link at the top right, and the "Scan photos" button on the
    next page. You should see the following messages:

    * Scanning path/to/myks-gallery/example/media/photos
    * Adding album 2023_01_01_Featured Pictures (Photos) as Featured Pictures
    * Done (0.01s)

    Go to http://localhost:8000/ and enjoy!

    Since you're logged in as an admin user, you can view albums and photos
    even though you haven't defined any access policies yet.

Changelog
=========

1.0
---

*Under development*

0.9
---

This version makes it possible to customize image resizing, for example to
integrate an external service, with the ``GALLERY_RESIZE`` setting. Review
``gallery.resizers.thumbor.resize`` for an example.

Several features designed for storing files in the filesystem are removed:

* The ``--resize`` option of ``django-admin scanphotos`` is removed.
* Expiration of album archives with the ``GALLERY_ARCHIVE_EXPIRY`` setting is
  removed. Configure lifecycle for the ``export`` folder on the cloud storage
  service instead.
* Fallback to the ``GALLERY_PHOTO_DIR`` and ``GALLERY_CACHE_DIR`` settings,
  deprecated in version 0.5, is removed.
* Support for serving files privately from the local filesystem is removed,
  including the ``GALLERY_SENDFILE_HEADER`` and ``GALLERY_SENDFILE_PREFIX``
  settings.

It includes smaller changes too.

* Updated for Django 4.0.

0.8
---

* Changed photo access policies to always override album access policies, even
  when "Photos inherit album access policy" is enabled. This makes it possible
  to restrict access with photo access policies, rather than just extend it.
* Updated for Django 3.0.

0.7
---

* Updated for Django 2.0.

0.6
---

* Added migrations for compatibility with Django 1.9.

To upgrade an existing project, run: ``django-admin migrate --fake-initial``.

0.5
---

This version uses the Django file storage API for all operations on files,
making it possible to use services such as Amazon S3 or Google Cloud Storage
for storing photos and thumbnails. It introduces the ``GALLERY_PHOTO_STORAGE``
and ``GALLERY_CACHE_STORAGE`` settings. They supersede ``GALLERY_PHOTO_DIR``
and ``GALLERY_CACHE_DIR``.

When upgrading to 0.5 or later, you should clear the cache directory.
Previously cached thumbnails and exports won't be used by this version.

It includes smaller changes too.

* Switched ordering of albums to always show the most recent albums first.
* Allowed customizing the number of photos in album previews.
* Preserved original order of photos in album previews.
* Added pagination on album preview pages.
* Changed the hashing schema. This invalides the cache. You should clear it.
* Fixed collision between zip archives containing photos with the same name.

0.4
---

* Provided exports of albums as zip archives.
* Fixed preview of photos affected by batch access policy changes.

0.3
---

* Support for Python 3 and Django 1.6.
* Hid public albums by default for logged-in users.
* Switched the default styles to a responsive design.
* Added an option to scanphotos to precompute thumbnails.
* Added an option to scanphotos to resynchronize photo dates.
* Fixed bugs in photo dates.

0.2
---

* Made most settings optional for easier deployment.
* Made "sendfile" optional and used streaming responses as a fallback.
* Worked around a crash in libjpeg when creating large JPEG previews.
* Added many tests.

0.1
---

* Initial public release, with the history from my private repository.
* Added documentation (README file).
* Added a sample application.

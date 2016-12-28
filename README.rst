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
.. _humble photo gallery: http://myks.org/photos/

Use case
========

Rather than use a photo manager, I just create a new directory for each event
and put my photos inside. I include the date of the event in the name of the
directory and I rename photos based on their date and time. Then I regularly
synchronize my collection to a remote storage. I serve my gallery from there.

If you have a similar workflow, you may find myks-gallery useful.

Whenever I upload new photos, I re-scan the collection with ``./manage.py
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

myks-gallery is a pluggable Django application. It requires Django ≥ 1.8 and
Pillow. It works with any version of Python supported by Django.

Architecture
------------

myks-gallery requires two storage areas:

- The first one contains the original photos. It's a read-only reference. You
  can upload photos there with `aws s3 sync`_, `gsutil rsync`_, rsync_, etc.
  depending on the platform. (I don't know any such tool for Azure storage.)
- The second one contains downscaled photos and ZIP archives of album exports.
  It's a read-write cache. You can set up expiry policies and clear it without
  affecting the gallery, aside from the cost of rescaling images again.

myks-gallery accesses them through Django's `file storage API`_, meaning that
you can use any storage for which a Django storage backend exists. You should
use a third-party storage backend if you're storing files in a cloud service
and Djang's built-in ``FileSystemStorage`` if you're storing them locally on
the filesystem, typically for local development.

.. _aws s3 sync: http://docs.aws.amazon.com/cli/latest/reference/s3/sync.html
.. _gsutil rsync: https://cloud.google.com/storage/docs/gsutil/commands/rsync
.. _rsync: http://rsync.samba.org/
.. _file storage API: https://docs.djangoproject.com/en/stable/ref/files/storage/

Installation guide
------------------

This application isn't exactly plug'n'play. There are many moving pieces.
Here's the general process for integrating myks-gallery into an existing
website:

1.  Download and install the package from PyPI::

        $ pip install myks-gallery

2.  Add ``gallery.apps.GalleryConfig`` to ``INSTALLED_APPS``::

        INSTALLED_APPS += 'gallery.apps.GalleryConfig',

3.  Configure the settings — see below for the list.

4.  Add the application to your URLconf with the ``gallery`` application
    namespace::

        urlpatterns += [
            url(r'^gallery/', include('gallery.urls', namespace='gallery', app_name='gallery')),
        ]

5.  Create a suitable ``base.html`` template. It must provide three blocks:
    ``title``, ``extrahead``, ``content``, as shown in this `example`_.

6.  Optionally, if you're serving files from the local filesystem, enable
    `X-accel`_ (nginx) or `mod_xsendfile`_ (Apache) for your photo and cache
    directories.

7.  Scan your photos with the "Scan photos" button in the admin or the
    ``scanphotos`` management command and define access policies.

The source_ contains a sample application in the ``example`` directory. It can
help you see how everything fits together. See below for how to run it.

.. _example: https://github.com/aaugustin/myks-gallery/blob/master/example/example/templates/base.html
.. _X-accel: http://wiki.nginx.org/X-accel
.. _mod_xsendfile: https://tn123.org/mod_xsendfile/
.. _source: https://github.com/aaugustin/myks-gallery

Permissions
-----------

myks-gallery defines two permissions:

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

For compatibility for versions prior to 0.5, if ``GALLERY_PHOTO_STORAGE``
isn't defined but ``GALLERY_PHOTO_DIR`` is, the photo storage will be set to
``FileSystemStorage(location=GALLERY_PHOTO_DIR)``.

``GALLERY_CACHE_STORAGE``
.........................

Default: *not defined*

Dotted Python path to the Django storage class for the thumbnails and album
archives. It must be readable and writable by the application server.

It behaves like ``GALLERY_PHOTO_STORAGE``.

For compatibility for versions prior to 0.5, if ``GALLERY_CACHE_STORAGE``
isn't defined but ``GALLERY_CACHE_DIR`` is, the photo storage will be set to
``FileSystemStorage(location=GALLERY_CACHE_DIR)``.

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

``GALLERY_RESIZE_PRESETS``
..........................

Default: ``{}``

Dictionary mapping thumbnail presets names to ``(width, height, crop)``. If
``crop`` is ``True``, the photo will be cropped and the thumbnail will have
exactly the requested size. If ``crop`` is ``False``, the thumbnaill will be
smaller than the requested size in one dimension to preserve the photo's
aspect ratio.

The default templates assume the following values::

    GALLERY_RESIZE_PRESETS = {
        'thumb': (128, 128, True),
        'standard': (768, 768, False),
    }

You may double these sizes for better results on high DPI displays.

``GALLERY_RESIZE_OPTIONS``
..........................

Default: ``{}``

Dictionary mapping image formats names to to dictionaries of options for
Pillow's ``save`` method. Options are described for each file format in
Pillow's documentation.

The following a reasonable value for high-quality thumbnails and previews::

    GALLERY_RESIZE_OPTIONS = {
        'JPEG': {'quality': 95, 'optimize': True},
    }

.. _options:

``GALLERY_SENDFILE_HEADER``
............................

Default: ``''``

Name of the HTTP header that triggers ``sendfile`` on your web server. Use
``'X-Accel-Redirect'`` for nginx and ``'X-SendFile'`` for Apache.

``GALLERY_SENDFILE_ROOT``
.........................

Default: ``''``

Part to strip at the beginning of the paths in the ``sendfile`` header. The
header will contain the absolute path to files, minus this prefix. This is
generally useful for nginx and not necessary for Apache.

``GALLERY_TITLE``
.................

Default: ``"Gallery"``

Title of your photo gallery. This is only used by the default templates of the
index and year views.

``GALLERY_PREVIEW_COUNT``
.........................

Default: ``5``

Number of thumbnails shown in the preview of each album.

``GALLERY_ARCHIVE_EXPIRY``
..........................

Default: ``None`` or ``60``

Duration in days during which album archives are kept in cache. ``None``
disables expiration.

When using a remote storage system such as S3, configuring an expiry policy
for the ``export`` folder directly on the storage system is more efficient.

For compatibility with versions prior to 0.5, if ``GALLERY_CACHE_DIR`` is
defined, ``GALLERY_ARCHIVE_EXPIRY`` defaults to ``60``.


Running the sample application
==============================

1.  Make sure Django and Pillow are installed

2.  Download some pictures (warning: these files are large, total = 50MB; you
    can use photos of your own instead as long as you respect the format of
    the directory name: ``YYYY_MM_DD_album name``)::

    $ cd example
    $ mkdir cache
    $ mkdir photos
    $ mkdir "photos/2013_01_01_Featured Pictures"
    $ cd "photos/2013_01_01_Featured Pictures"
    $ wget http://upload.wikimedia.org/wikipedia/commons/5/51/2012-11-23_16-05-52-grande-cascade-tendon.jpg
    $ wget http://upload.wikimedia.org/wikipedia/commons/5/56/Crooked_Beak_of_Heaven_Mask.jpg
    $ wget http://upload.wikimedia.org/wikipedia/commons/a/a4/Iglesia_de_Nuestra_Se%C3%B1ora_de_La_Blanca%2C_Cardej%C3%B3n%2C_Espa%C3%B1a%2C_2012-09-01%2C_DD_02.   JPG
    $ wget http://upload.wikimedia.org/wikipedia/commons/1/17/Iglesia_del_Esp%C3%ADritu_Santo%2C_Landshut%2C_Alemania%2C_2012-05-27%2C_DD_02.JPG
    $ wget http://upload.wikimedia.org/wikipedia/commons/3/33/Viru_Bog%2C_Parque_Nacional_Lahemaa%2C_Estonia%2C_2012-08-12%2C_DD_60.JPG
    $ wget http://upload.wikimedia.org/wikipedia/commons/d/d7/Castillo_Trausnitz%2C_Landshut%2C_Alemania%2C_2012-05-27%2C_DD_18.JPG
    $ wget http://upload.wikimedia.org/wikipedia/commons/b/b7/Catedral_de_Alejandro_Nevsky%2C_Tallin%2C_Estonia%2C_2012-08-11%2C_DD_46.JPG
    $ wget http://upload.wikimedia.org/wikipedia/commons/3/3f/Crassula_arborescens%2C_Jard%C3%ADn_Bot%C3%A1nico%2C_M%C3%BAnich%2C_Alemania_2012-04-21%2C_DD_01.JPG
    $ wget http://upload.wikimedia.org/wikipedia/commons/8/86/Plaza_del_ayuntamiento%2C_Set%C3%BAbal%2C_Portugal%2C_2012-08-17%2C_DD_01.JPG
    $ wget http://upload.wikimedia.org/wikipedia/commons/7/71/4_cilindros_y_museo_BMW%2C_M%C3%BAnich%2C_Alemania_2012-04-28%2C_DD_02.JPG
    $ cd ../..

3.  Run the development server::

    $ ./manage.py migrate
    $ ./manage.py runserver

4.  Go to http://localhost:8000/admin/gallery/album/ and log in. Click the
    "Scan photos" link at the top right, and the "Scan photos" button on the
    next page. You should see the following messages:

    * Scanning path/to/myks-gallery/example/photos
    * Adding album 2013_01_01_Featured Pictures (Photos) as Featured Pictures
    * Done (0.01s)

    Go to http://localhost:8000/ and enjoy!

    Since you're logged in as an admin user, you can view albums and photos
    even though you haven't defined any access policies yet.

Changelog
=========

0.7
---

*Under development*

0.6
---

* Added migrations for compatibility with Django 1.9.

0.5
---

This version uses the Django file storage API for all operations on files,
making it possible to use services such as Amazon S3 or Google Cloud Storage
for storing photos and thumbnails. It introduces the ``GALLERY_PHOTO_STORAGE``
and ``GALLERY_CACHE_STORAGE`` settings. They supersede ``GALLERY_PHOTO_DIR``
and ``GALLERY_CACHE_DIR``.

When upgrading to 0.5 or later, you should clear the cache directory.
Previously cached thumbnails and exports won't be used by this version.

It also include some smaller changes.

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

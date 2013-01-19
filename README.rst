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
directory and I rename photos based on their date and time. I regularly
synchronize my collection to a server with rsync_.

.. _rsync: http://rsync.samba.org/

If you have a similar workflow, you may find myks-gallery useful.

Whenever I upload new photos, I re-scan the collection with ``./manage.py
scanphotos``, and myks-gallery detects new albums and photos. Then I can
define users, groups and access policies in the admin.

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

myks-gallery is a pluggable Django application. It requires Python 2.6 or 2.7,
Django 1.5, and PIL.

Installation guide
------------------

This application isn't exactly plug'n'play. There are many moving pieces.
Here's the general process for integrating myks-gallery into an existing
website:

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

5.  Create a suitable ``base.html`` template. It must provide three blocks:
    ``title``, ``extrahead``, ``content``, as shown in this `example`_.

6.  Enable `X-accel`_ (nginx) or `mod_xsendfile`_ (Apache) for your photo and
    cache directories (``GALLERY_PHOTO_DIR`` and ``GALLERY_CACHE_DIR``).

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

Running the sample application
==============================

1.  Make sure Django and PIL are installed

2.  Download some pictures (warning: these files are large, total = 50MB; you
    can use photos of your own instead as long as you respect the format of
    the directory name: ``YYYY_MM_DD_album name``)::

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

    $ ./manage.py syncdb
    $ ./manage.py runserver

4.  Go to http://localhost:8000/admin/gallery/album/ and log in. Click the
    "Scan photos" link at the top right, and the "Scan photos" button on the
    next page. You should see the following messages:

        Scanning .../myks-gallery/example/photos

        Adding album 2013_01_01_Featured Pictures (Photos) as Featured Pictures

        Done (0.01s)

    Now go to http://localhost:8000/ and enjoy!

    Since you're logged in as an admin user, you can view albums and photos
    even though you haven't defined any access policies yet.

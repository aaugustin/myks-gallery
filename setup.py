import distutils.core
import os

# Avoid polluting the .tar.gz with ._* files under Mac OS X
os.putenv('COPYFILE_DISABLE', 'true')

description = 'Photo gallery with granular access control'

with open(os.path.join(os.path.dirname(__file__), 'README')) as f:
    long_description = '\n\n'.join(f.read().split('\n\n')[2:7])

distutils.core.setup(
    name='myks-gallery',
    version='0.2',
    author='Aymeric Augustin',
    author_email='aymeric.augustin@m4x.org',
    url='https://github.com/aaugustin/myks-gallery',
    description=description,
    long_description=long_description,
    download_url='http://pypi.python.org/pypi/myks-gallery',
    packages=[
        'gallery',
        'gallery.management',
        'gallery.management.commands',
        'gallery.tests',
    ],
    package_data={
        'gallery': [
            'locale/*/LC_MESSAGES/*',
            'static/css/gallery.css',
            'templates/admin/gallery/*.html',
            'templates/gallery/*.html',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
    ],
    platforms='all',
    license='BSD'
)

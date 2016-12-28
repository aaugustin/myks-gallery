import codecs
import os.path

import setuptools

root_dir = os.path.abspath(os.path.dirname(__file__))

description = "Photo gallery with granular access control"

with codecs.open(os.path.join(root_dir, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


setuptools.setup(
    name='myks-gallery',
    version='0.6.1',
    description=description,
    long_description=long_description,
    url='https://github.com/aaugustin/myks-gallery',
    author='Aymeric Augustin',
    author_email='aymeric.augustin@m4x.org',
    license='BSD',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    packages=[
        'gallery',
        'gallery.management',
        'gallery.management.commands',
        'gallery.migrations',
    ],
    package_data={
        'gallery': [
            'locale/*/LC_MESSAGES/*',
            'static/css/gallery.css',
            'templates/admin/gallery/*.html',
            'templates/gallery/*.html',
        ],
    },
)

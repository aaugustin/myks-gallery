# Copyright (c) 2011-2012 Aymeric Augustin. All rights reserved.

import StringIO

from django.conf.urls import patterns, url
from django.contrib import admin
from django.contrib.auth.decorators import permission_required
from django.contrib import messages
from django.core import management
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import ugettext as _

from .models import Album, AlbumAccessPolicy, Photo, PhotoAccessPolicy


@permission_required('gallery.scan')
def scan_photos(request):
    if request.method == 'POST':
        stdout, stderr = StringIO.StringIO(), StringIO.StringIO()
        management.call_command('scanphotos', stdout=stdout, stderr=stderr)
        for line in stdout.getvalue().splitlines():
            messages.info(request, line)
        for line in stderr.getvalue().splitlines():
            messages.error(request, line)
        return HttpResponseRedirect(reverse('admin:gallery.admin.scan_photos'))
    context = {
        'title': _("Scan photos"),
    }
    return render(request, 'admin/gallery/scan_photos.html', context)


class ScanUrlMixin(object):
    def get_urls(self):
        return patterns('',
            url(r'^scan/$', scan_photos),
        ) + super(ScanUrlMixin, self).get_urls()


class AccessPolicyInline(admin.StackedInline):
    filter_horizontal = ('groups', 'users')


class AlbumAccessPolicyInline(AccessPolicyInline):
    model = AlbumAccessPolicy

class AlbumAdmin(ScanUrlMixin, admin.ModelAdmin):
    date_hierarchy = 'date'
    inlines = (AlbumAccessPolicyInline,)
    list_display = ('dirpath', 'date', 'name', 'category')
    list_filter = ('category',)
    ordering = ('-date',)
    search_fields = ('name', 'dirpath')

admin.site.register(Album, AlbumAdmin)


class PhotoAccessPolicyInline(AccessPolicyInline):
    model = PhotoAccessPolicy

class PhotoAdmin(ScanUrlMixin, admin.ModelAdmin):
    date_hierarchy = 'date'
    inlines = (PhotoAccessPolicyInline,)
    list_display = ('filename', 'date')
    ordering = ('date',)
    readonly_fields = ('filename',)
    search_fields = ('album__name', 'filename')

admin.site.register(Photo, PhotoAdmin)

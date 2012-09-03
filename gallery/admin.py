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
from django.template import Context, Template
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
    list_display = ('display_name', 'date', 'category', 'public', 'groups', 'users', 'inherit')
    list_filter = ('category',)
    ordering = ('-date', '-name', '-dirpath', '-category')
    readonly_fields = ('dirpath',)
    search_fields = ('name', 'dirpath')

    def queryset(self, request):
        return (super(AlbumAdmin, self).queryset(request)
                .prefetch_related('access_policy__users')
                .prefetch_related('access_policy__groups'))

    def public(self, obj):
        access_policy = obj.get_access_policy()
        if access_policy:
            return access_policy.public
    public.boolean = True

    def groups(self, obj):
        access_policy = obj.get_access_policy()
        if access_policy:
            groups = access_policy.groups.all()
            return u', '.join(unicode(group) for group in groups)
        else:
            return '-'

    def users(self, obj):
        access_policy = obj.get_access_policy()
        if access_policy:
            users = access_policy.users.all()
            return u', '.join(unicode(user) for user in users)
        else:
            return '-'

    def inherit(self, obj):
        access_policy = obj.get_access_policy()
        if access_policy:
            return access_policy.inherit
    inherit.boolean = True

admin.site.register(Album, AlbumAdmin)


class PhotoAccessPolicyInline(AccessPolicyInline):
    model = PhotoAccessPolicy

class PhotoAdmin(ScanUrlMixin, admin.ModelAdmin):
    date_hierarchy = 'date'
    inlines = (PhotoAccessPolicyInline,)
    list_display = ('display_name', 'date', 'preview', 'public', 'groups', 'users')
    ordering = ('-date', '-filename')
    readonly_fields = ('filename',)
    search_fields = ('album__name', 'album__dirpath', 'filename')

    def queryset(self, request):
        return (super(PhotoAdmin, self).queryset(request)
                .prefetch_related('access_policy__users')
                .prefetch_related('access_policy__groups')
                .prefetch_related('album__access_policy__users')
                .prefetch_related('album__access_policy__groups'))

    preview_template = Template("""{% load url from future %}"""
"""<a href="{{ photo.get_absolute_url }}">"""
"""<img src="{% url 'gallery-photo-resized' preset='thumb' pk=photo.pk %}" width="128" height="128" alt="{{ photo }}">"""
"""</a>""")

    def preview(self, obj):
        return self.preview_template.render(Context({'photo': obj}))
    preview.allow_tags = True

    def public(self, obj):
        access_policy = obj.get_effective_access_policy()
        if access_policy:
            return access_policy.public
    public.boolean = True

    def groups(self, obj):
        access_policy = obj.get_effective_access_policy()
        if access_policy:
            return u', '.join(unicode(group) for group in access_policy.groups.all())
        else:
            return '-'

    def users(self, obj):
        access_policy = obj.get_effective_access_policy()
        if access_policy:
            return u', '.join(unicode(user) for user in access_policy.users.all())
        else:
            return '-'

admin.site.register(Photo, PhotoAdmin)

# Copyright (c) 2011-2012 Aymeric Augustin. All rights reserved.

from django.contrib import admin

from .models import Album, AlbumAccessPolicy, Photo, PhotoAccessPolicy


class AccessPolicyInline(admin.StackedInline):
    filter_horizontal = ('groups', 'users')


class AlbumAccessPolicyInline(AccessPolicyInline):
    model = AlbumAccessPolicy

class AlbumAdmin(admin.ModelAdmin):
    date_hierarchy = 'date'
    inlines = (AlbumAccessPolicyInline,)
    list_display = ('dirpath', 'date', 'name', 'category')
    list_filter = ('category',)
    ordering = ('-date',)
    search_fields = ('name', 'dirpath')

admin.site.register(Album, AlbumAdmin)


class PhotoAccessPolicyInline(AccessPolicyInline):
    model = PhotoAccessPolicy

class PhotoAdmin(admin.ModelAdmin):
    date_hierarchy = 'date'
    inlines = (PhotoAccessPolicyInline,)
    list_display = ('filename', 'date')
    ordering = ('date',)
    readonly_fields = ('filename',)
    search_fields = ('album__name', 'filename')

admin.site.register(Photo, PhotoAdmin)

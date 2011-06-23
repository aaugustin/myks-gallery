# Copyright (c) 2011 Aymeric Augustin. All rights reserved.

from django.contrib import admin

from .models import Album, Photo


class AlbumAdmin(admin.ModelAdmin):
    date_hierarchy = 'date'
    list_display = ('dirpath', 'date', 'name')
    ordering = ('-date',)
    readonly_fields = ('dirpath',)
    search_fields = ('name', 'dirpath')

admin.site.register(Album, AlbumAdmin)


class PhotoAdmin(admin.ModelAdmin):
    date_hierarchy = 'date'
    list_display = ('filename', 'date')
    ordering = ('date',)
    readonly_fields = ('filename',)
    search_fields = ('album__name', 'filename')

admin.site.register(Photo, PhotoAdmin)

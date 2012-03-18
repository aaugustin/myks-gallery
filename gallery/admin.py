# Copyright (c) 2011-2012 Aymeric Augustin. All rights reserved.

from django.contrib import admin

from .models import Album, Photo


class PhotoInline(admin.TabularInline):
    extra = 0
    model = Photo

class AlbumAdmin(admin.ModelAdmin):
    date_hierarchy = 'date'
    inlines = (PhotoInline,)
    list_display = ('dirpath', 'date', 'name', 'category')
    list_filter = ('category',)
    ordering = ('-date',)
    search_fields = ('name', 'dirpath')

admin.site.register(Album, AlbumAdmin)


class PhotoAdmin(admin.ModelAdmin):
    date_hierarchy = 'date'
    list_display = ('filename', 'date')
    ordering = ('date',)
    readonly_fields = ('filename',)
    search_fields = ('album__name', 'filename')

admin.site.register(Photo, PhotoAdmin)

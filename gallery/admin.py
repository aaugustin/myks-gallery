# Copyright (c) 2011 Aymeric Augustin. All rights reserved.

from django.contrib import admin

from .models import Album, Photo


class AlbumAdmin(admin.ModelAdmin):
    ordering = ('-date',)

admin.site.register(Album, AlbumAdmin)


class PhotoAdmin(admin.ModelAdmin):
    ordering = ('date',)

admin.site.register(Photo, PhotoAdmin)

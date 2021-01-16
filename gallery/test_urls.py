from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    # insecure - only for testing!
    path('private<path:path>', views.serve_private_media),
    path('', include('gallery.urls', namespace='gallery')),
]

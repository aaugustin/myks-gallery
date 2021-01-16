from django.urls import path

from . import views

app_name = 'gallery'

urlpatterns = [
    path('', views.GalleryIndexView.as_view(), name='index'),
    path('latest/', views.latest_album, name='latest'),
    path('year/<int:year>/', views.GalleryYearView.as_view(), name='year'),
    path('album/<int:pk>/', views.AlbumView.as_view(), name='album'),
    path('export/<int:pk>/', views.export_album, name='album-export'),
    path('photo/<int:pk>/', views.PhotoView.as_view(), name='photo'),
    path('original/<int:pk>/', views.original_photo, name='photo-original'),
    path('resized/<slug:preset>/<int:pk>/', views.resized_photo, name='photo-resized'),
]

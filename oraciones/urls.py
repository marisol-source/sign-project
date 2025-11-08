# oraciones/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('guardar_oracion/', views.guardar_oracion, name='guardar_oracion'),
]

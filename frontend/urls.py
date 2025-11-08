from . import views
from django.urls import path

from oraciones import views as oraciones_views 

urlpatterns = [
    path("", views.home, name="home"),
    path('demo/', views.prototipo, name='demo'),
    path('modelo_premium/', views.modelo_premium, name='modelo_premium'),  # Nueva ruta
    path("login/", views.login_view, name="login"),  
    path('registro/', views.registro, name='registro'),
    path('guardar_oracion/', oraciones_views.guardar_oracion, name='guardar_oracion'),


]
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path('demo/', views.prototipo, name='demo'),
    path("login/", views.login_view, name="login"),  
    path('registro/', views.registro, name='registro'),

]
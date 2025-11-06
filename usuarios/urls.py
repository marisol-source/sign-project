from django.urls import path
from . import views

urlpatterns = [
    path('registro/', views.registrar_empresa, name='registro'),
    path('login/', views.login_empresa, name='login_empresa'),
    path('logout/', views.logout_empresa, name='logout'),
]

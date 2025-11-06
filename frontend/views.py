"""Importamos la función  desde usuarios.views y la usamos en la vista de registro."""

from django.shortcuts import render
from usuarios.views import registrar_empresa #Este método es del contexto de arriba


def home(request):
    return render(request, 'index.html')

def prototipo(request):
    return render(request, 'prototipo/modelo.html')

def login_view(request):
    return render(request, "auth/login.html")

def registro(request):
    """Si el método es POST, delega la lógica al backend para registrar la empresa."""
    if request.method == 'POST':
        return registrar_empresa(request)
    return render(request, 'auth/registro.html')

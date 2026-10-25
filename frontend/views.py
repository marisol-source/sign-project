"""Importamos la función  desde usuarios.views y la usamos en la vista de registro."""

from django.shortcuts import render
from usuarios.views import registrar_empresa #Este método es del contexto de arriba
from oraciones.views import guardar_oracion
from django.contrib.auth.decorators import login_required


def home(request):
    """Renderiza la página de inicio."""
    return render(request, 'index.html')

def login_view(request):
    """Si el método es POST, delega la lógica al backend para iniciar sesión."""
    return render(request, "auth/login.html")

def registro(request):
    """Si el método es POST, delega la lógica al backend para registrar la empresa."""
    if request.method == 'POST':
        return registrar_empresa(request)
    return render(request, 'auth/registro.html')

def prototipo(request):
    """Renderiza la página del prototipo."""
    return render(request, 'prototipo/modelo.html')

 # Redirige a la página de login si no está logueado
def modelo_premium(request):
    """Renderiza la página del modelo premium."""
    return render(request, 'prototipo/modelo_premium.html')

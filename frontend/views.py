from django.shortcuts import render

def home(request):
    return render(request, 'index.html')

def prototipo2(request):
    return render(request, 'prototipo/prototipo2.html')

def login_view(request):
    return render(request, "auth/login.html")

def registro(request):
    return render(request, 'auth/registro.html')
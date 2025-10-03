from django.shortcuts import render

def home(request):
    return render(request, 'home.html')

def prototipo2(request):
    return render(request, 'prototipo2.html')
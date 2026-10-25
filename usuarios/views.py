"""Vistas relacionadas con la autenticación de empresas."""
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Empresa

def registrar_empresa(request):
    """Registra una nueva empresa en la base de datos."""
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        correo = request.POST.get('email')
        contrasena = request.POST.get('password')
        contrasena2 = request.POST.get('password2')

        # Validación: contraseñas iguales
        if contrasena != contrasena2:
            messages.error(request, "Las contraseñas no coinciden.")
            # no crear ni redirigir, solo volver al formulario
            return render(request, 'auth/registro.html', {
                'nombre': nombre,
                'email': correo
            })

        # Validación: correo existente
        if Empresa.objects.filter(correo=correo).exists():
            messages.error(request, "El correo ya está registrado.")
            return render(request, 'auth/registro.html', {
                'nombre': nombre,
                'email': correo
            })

        # Si pasa las validaciones, recién crea la empresa
        Empresa.objects.create(
            nombre=nombre,
            correo=correo,
            contrasena=contrasena  # luego se encripta
        )

        messages.success(request, "Tu cuenta ha sido creada exitosamente.")
        return redirect('login')

    return render(request, 'auth/registro.html')

def login_empresa(request):
    """Inicia sesión de una empresa existente."""
    storage = messages.get_messages(request)
    storage.used = True

    if request.method == 'POST':
        correo = request.POST.get('email')
        contrasena = request.POST.get('password')
        try:
            empresa = Empresa.objects.get(correo=correo)
        except Empresa.DoesNotExist:
            messages.error(request, "Correo no registrado.")
            return render(request, 'auth/login.html', {'email': correo})

        if empresa.contrasena != contrasena:
            messages.error(request, "Contraseña incorrecta.")
            return render(request, 'auth/login.html', {'email': correo})

        # Si todo es correcto → logeado
        request.session['empresa_id'] = empresa.id
        request.session['empresa_nombre'] = empresa.nombre
        
        # Agregar mensaje de bienvenida
        messages.success(request, f"Bienvenido, {empresa.nombre}!")
        return render(request, 'logeado.html', {'empresa_nombre': empresa.nombre})

    # Si es GET → mostrar el login normal
    return render(request, 'auth/login.html')

def logout_empresa(request):
    """Cierra sesión limpiando mensajes y sesión."""
     # 🔹 Limpiar mensajes pendientes antes de cerrar sesión
    storage = messages.get_messages(request)
    for _ in storage:
        pass  # consumir los mensajes
    storage.used = True

    # Borrar sesión completa
    request.session.flush()
    # Redirige al index del frontend
    return redirect('/')

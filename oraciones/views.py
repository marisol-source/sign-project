# oraciones/views.py

from django.shortcuts import render
from django.http import JsonResponse
from .models import Oracion
from usuarios.models import Empresa  # Importamos el modelo Empresa
from django.contrib.auth.decorators import login_required
import json  # 
from usuarios.models import Empresa  # 👈 asegúrate de tener esto arriba



 # Solo permitir si el usuario está logueado
def guardar_oracion(request):
    if request.method == 'POST':
        print("📥 Se recibió un POST en guardar_oracion")  # 👈 Depuración

        try:
            data = json.loads(request.body)
            print("📦 Datos recibidos:", data)  # 👈 Para ver qué llegó exactamente
        except Exception as e:
            print("❌ Error al leer JSON:", e)
            return JsonResponse({'status': 'error', 'message': 'JSON inválido'}, status=400)

        oracion_original = data.get('oracion_original')
        oracion_corregida = data.get('oracion_corregida')
        print("🧠 Original:", oracion_original)
        print("🧠 Corregida:", oracion_corregida)

        # 🔹 Por ahora no usemos el usuario, para descartar fallos allí:
        empresa_id = request.session.get('empresa_id')
        if not empresa_id:
            print("⚠️ No se encontró empresa_id en la sesión.")
            return JsonResponse({'status': 'error', 'message': 'Sesión expirada o no iniciada.'}, status=403)

        empresa = Empresa.objects.get(id=empresa_id)

        Oracion.objects.create(
            empresa=empresa,
            oracion_original=oracion_original,
            oracion_corregida=oracion_corregida
        )    

        return JsonResponse({'status': 'success', 'message': 'Oración guardada exitosamente'})

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=400)
# oraciones/views.py
from django.shortcuts import render
from django.http import JsonResponse
from .models import Oracion
from usuarios.models import Empresa  # Importamos el modelo Empresa
from django.contrib.auth.decorators import login_required
import json  # 
from usuarios.models import Empresa  # 👈 asegúrate de tener esto arriba
from django.views.decorators.csrf import csrf_exempt
from hand_recognition.iscs import calcular_iscs  


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

        oracion=Oracion.objects.create(
            empresa=empresa,
            oracion_original=oracion_original,
            oracion_corregida=oracion_corregida,
        )   
        print("✅ Oración guardada en BD con ID:", oracion.id)
        return JsonResponse({'status': 'success','oracion_id': oracion.id,'message': 'Oración guardada exitosamente'})

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=400)



@csrf_exempt
def guardar_feedback(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            oracion_id = data.get("oracion_id")
            resultado = data.get("resultado_esperado")

            oracion = Oracion.objects.get(id=oracion_id)
            oracion.resultado_esperado = resultado


             # 🔹 CALCULAR ISCS
            iscs_data = calcular_iscs(
                oracion.oracion_original,
                oracion.oracion_corregida,
                resultado
            )

            # 🔹 Guardar métricas (ejemplo)
            oracion.iscs_final = iscs_data["iscs_final"]
            oracion.iscs_intencion = iscs_data["intencion"]
            oracion.iscs_contexto = iscs_data["contexto"]
            oracion.iscs_reglas = iscs_data["reglas_tecnicas"]

            oracion.save()

            return JsonResponse({"status": "success","iscs": iscs_data})
        except Oracion.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Oración no encontrada"}, status=404)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)
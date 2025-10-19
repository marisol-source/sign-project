from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import random

@csrf_exempt  # <--- esto quita la protección CSRF solo para esta vista
def predict(request):
    if request.method == "POST":
        return JsonResponse({
            "letter": random.choice(["A","B","C"]),
            "confidence": random.random()
        })
    return JsonResponse({"error": "Método no permitido"}, status=405)


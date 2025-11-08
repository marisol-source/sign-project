# oraciones/models.py

from django.db import models
from usuarios.models import Empresa  # Importamos el modelo Empresa de la app 'usuarios'

class Oracion(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)  # Relacionamos con la empresa
    oracion_original = models.TextField()  # Oración original
    oracion_corregida = models.TextField()  # Oración corregida por el sistema
    created_at = models.DateTimeField(auto_now_add=True)  # Fecha de creación
    updated_at = models.DateTimeField(auto_now=True)  # Fecha de la última actualización

    def __str__(self):
        return f'Oración de {self.empresa.nombre} - {self.created_at}'

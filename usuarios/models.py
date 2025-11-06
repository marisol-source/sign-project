"""Definimos el modelo de Empresa para la base de datos."""
from django.db import models

class Empresa(models.Model):
    """Definimos los atributos que sera una una columna en la base de datos."""
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la empresa o corporación")
    correo = models.EmailField(unique=True, verbose_name="Correo electrónico")
    contrasena = models.CharField(max_length=255, verbose_name="Contraseña")


    def __str__(self):
        return str(self.nombre)

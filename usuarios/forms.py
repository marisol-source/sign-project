"""Formulario para registrar una nueva empresa o corporación (No lo uso)"""
from django import forms
from .models import Empresa

class EmpresaForm(forms.ModelForm):
    """Campos para que el usuario ingrese y confirme su contraseña."""
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirmar contraseña")

    class Meta:
        model = Empresa
        fields = ['nombre', 'correo', 'contrasena']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")

        if password and password2 and password != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data

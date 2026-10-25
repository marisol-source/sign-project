"""Docstring for hand_recognition.iscs""" 
import re

def evaluar_intencion(original, corregida):
    """Evalúa si la intención de la oración original se mantiene en la corregida."""
    return int(bool(original.strip()) and bool(corregida.strip()))

def evaluar_contexto(corregida):
    """Evalúa si la oración corregida contiene palabras clave de contexto."""
    palabras_contexto = [
        "quiero", "necesito", "solicito",
        "ayuda", "información", "consulta",
        "problema", "servicio", "pedido"
    ]
    texto = corregida.lower()
    return int(any(p in texto for p in palabras_contexto))

def evaluar_reglas_tecnicas(corregida):
    """Evalúa si la oración corregida cumple con reglas técnicas básicas."""
    palabras = corregida.split()
    cumple_longitud = len(palabras) <= 6
    primera_persona = bool(re.match(r"^(yo|nosotros)\b", corregida.lower()))
    return int(cumple_longitud and primera_persona)

def calcular_iscs(oracion_original, oracion_corregida, feedback_usuario):
    """
    feedback_usuario: True (Sí) o False (No)
    """
    intencion = evaluar_intencion(oracion_original, oracion_corregida)
    contexto = evaluar_contexto(oracion_corregida)
    reglas = evaluar_reglas_tecnicas(oracion_corregida)

    iscs = round((intencion + contexto + reglas) / 3, 2)

    return {
        "intencion": intencion,
        "contexto": contexto,
        "reglas_tecnicas": reglas,
        "feedback_usuario": feedback_usuario,
        "iscs_final": iscs
    }

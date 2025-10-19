# voice.py

import pyttsx3
import time

# Inicializamos el motor de pyttsx3
engine = pyttsx3.init()

# Configuración de la voz (seleccionar voz femenina, por ejemplo)
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)  # Cambiar al índice de la voz que prefieras (0 = masculina, 1 = femenina)

# Función para hablar la oración corregida
def hablar_oracion(texto):
    """Convierte texto a voz."""
    print("Hablando:", texto)  # Depuración
    engine.setProperty('volume', 1)  # Volumen: 0.0 a 1.0
    engine.setProperty('rate', 150)  # Velocidad de habla: 100-200 es un rango típico
    engine.say(texto)
    engine.runAndWait()

# Función para gestionar la inactividad y la corrección
def manejar_inactividad(last_detection_time, texto_corregido):
    """Detecta si han pasado 4 segundos de inactividad y habla la oración."""
    if time.time() - last_detection_time >= 4:  # Si han pasado 4 segundos sin detectar nuevas letras
        if texto_corregido.strip():  # Verifica que haya texto corregido
            hablar_oracion(texto_corregido)  # Habla la oración corregida
        last_detection_time = time.time()  # Reinicia el temporizador
    return last_detection_time

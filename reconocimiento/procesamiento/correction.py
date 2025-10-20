import google.generativeai as genai
import os
import time

# Configurar la API Key
API_KEY = "AIzaSyCEzyPeJ36oc2bB2Wopso5QLWTahjLGjoo"

def corregir_texto_automatico(texto):
    """Usa la API de Google Gemini para corregir el texto - Versión simplificada"""
    
    # Si el texto está vacío, retornar vacío
    if not texto or not texto.strip():
        return ""
    
    print(f"📨 Enviando a Gemini: '{texto}'")
    
    try:
        # Configurar el cliente
        genai.configure(api_key=API_KEY)
        
        # Configurar el modelo
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Prompt mejorado
        prompt = f"""
        Eres un intérprete de comunicación y corrector ortográfico/tipográfico. Tu rol es actuar como la voz clara y precisa de una persona sorda o con discapacidad auditiva que se está comunicando en un entorno de atención al cliente.
        Recibirás una palabra o frase que puede contener errores (ej: "paamn poyo"). Tu tarea es:
         1. Corregir internamente el error tipográfico o de deletreo.
         2. Transformar la corrección en una oración completa de servicio al cliente que refleje la **intención de la persona que se comunica**.
         Reglas de Output:
         1. La oración final debe tener un **máximo estricto de seis (6) palabras**.
        2. El **ÚNICO resultado** que debes proporcionar es la oración interpretada, hablada **en primera persona** (Yo/Nosotros).
        3. NO incluyas tablas, explicaciones, la palabra original, la corrección, ni ningún texto adicional.

    Interpreta la siguiente palabra(s) que te proporcionaré, siguiendo estas reglas.
      "{texto}"
        
        """

        # Hacer la solicitud
        response = model.generate_content(prompt)
        
        # Procesar respuesta
        if response and response.text:
            texto_corregido = response.text.strip()
            
            # Limitar a 6 palabras y formatear
            palabras = texto_corregido.split()[:6]
            texto_corregido = " ".join(palabras)
            
            # Capitalizar y agregar puntuación si es necesario
            texto_corregido = texto_corregido.capitalize()
            if not texto_corregido.endswith(('.', '!', '?')):
                texto_corregido += '.'
                
            print(f"✅ Gemini respondió: '{texto_corregido}'")
            return texto_corregido
        else:
            print("❌ Gemini no devolvió respuesta")
            return texto

    except Exception as e:
        print(f"❌ Error con Gemini: {e}")
        # Fallback: devolver el texto original con formato básico
        palabras = texto.split()[:6]
        texto_fallback = " ".join(palabras).capitalize()
        if not texto_fallback.endswith('.'):
            texto_fallback += '.'
        return texto_fallback
# utils.py

def polish_text(s: str) -> str:
    """Pulido mínimo: convertir todo a minúsculas y hacer mayúscula la primera letra de cada oración."""
    if not s:
        return s
    
    # Eliminar espacios extra y asegurar que la oración esté limpia
    txt = " ".join(s.split())
    
    # Convertir todo el texto a minúsculas
    txt = txt.lower()

    # Dividir en partes por punto (para manejar cada oración por separado)
    parts = [p.strip() for p in txt.split(".")]
    
    # Capitalizar la primera palabra de la primera oración
    if parts:
        parts[0] = parts[0].capitalize()

    # Unir las oraciones y agregar punto al final si falta
    txt = ". ".join(parts).strip()

    # Asegurarse de que termine con un punto
    if not txt.endswith("."):
        txt += "."

    return txt

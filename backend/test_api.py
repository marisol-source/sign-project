import requests

# Cambia las coordenadas según tu modelo
# ejemplo con 10 valores (pueden ser cualquier número solo para probar)
coords_prueba = [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0]

respuesta = requests.post(
    "http://127.0.0.1:8000/predecir",
    json={"coords": coords_prueba}
)

print(respuesta.json())

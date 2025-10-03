from fastapi import FastAPI
from pydantic import BaseModel
import joblib

# Cargar modelo
modelo = joblib.load("modelo_entrenado.pkl")

# Crear la API
app = FastAPI()

# Modelo de datos que espera la API
class Mano(BaseModel):
    coords: list  # vector plano con los datos de la mano

@app.post("/predecir")
def predecir_mano(mano: Mano):
    try:
        # Asegúrate de pasar un array 2D al modelo
        pred = modelo.predict([mano.coords])
        return {"prediccion": pred[0]}
    except Exception as e:
        return {"error": str(e)}

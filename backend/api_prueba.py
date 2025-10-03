from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import numpy as np

app = FastAPI()

# Permitir CORS para tu frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # temporalmente, para pruebas
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar modelo
modelo = joblib.load("modelo_entrenado.pkl")  # <- asegúrate de la ruta correcta

# Modelo de datos REST
class Mano(BaseModel):
    coords: list  # lista de 10 features

# Endpoint REST
@app.post("/predecir")
def predecir_mano(mano: Mano):
    try:
        pred = modelo.predict([mano.coords])
        return {"prediccion": pred[0]}
    except Exception as e:
        return {"error": str(e)}

# WebSocket
@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_json()
            # Aquí recibes los frames del frontend (base64)
            frame = data.get("frame")
            if frame:
                # 🔹 Para prueba, podemos simular predicción con valores aleatorios
                # En producción, procesar frame con MediaPipe y extraer coords
                fake_coords = np.random.rand(10).tolist()
                pred = modelo.predict([fake_coords])[0]
                await websocket.send_json({"letter": pred})
        except Exception as e:
            await websocket.send_json({"error": str(e)})

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
from reconocimiento.recognition import extract_features, predict_letter

app = FastAPI()

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Esquema que recibe los landmarks
class Mano(BaseModel):
    landmarks: list  # lista de 21 puntos [{x,y,z}, ...]

@app.post("/predecir")
def predecir_mano(mano: Mano):
    try:
        # Convertir landmarks en numpy array
        pts = np.array([[lm["x"], lm["y"], lm["z"]] for lm in mano.landmarks], dtype=np.float32)

        # Extraer características
        feats = extract_features(pts)

        # Predecir con tu modelo ya cargado en recognition.py
        letra, confianza = predict_letter(feats)

        return {"prediccion": letra, "confianza": float(confianza)}
    except Exception as e:
        return {"error": str(e)}

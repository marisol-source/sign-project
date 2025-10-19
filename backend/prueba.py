from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
import joblib
import numpy as np

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar modelo y scaler
mlp = joblib.load("modelo_entrenado.pkl")
scaler = joblib.load("scaler.pkl")
FEATURE_ORDER = ['thumb_open', 'idx_open', 'mid_open', 'ring_open', 'pinky_open',
                 'thumb_fold', 'idx_fold', 'mid_fold', 'ring_fold', 'pinky_fold']

class Landmarks(BaseModel):
    landmarks: List[List[float]]  # lista de [x, y, z]

# Funciones de extracción y predicción (igual que antes)
def pair_dist(pts, a, b):
    pa, pb = pts[a][:2], pts[b][:2]
    return float(np.linalg.norm(pa - pb))

def angle(a, b, c, pts):
    A, B, C = pts[a][:2], pts[b][:2], pts[c][:2]
    BA, BC = A - B, C - B
    denom = (np.linalg.norm(BA) * np.linalg.norm(BC) + 1e-8)
    cosang = np.dot(BA, BC) / denom
    cosang = np.clip(cosang, -1.0, 1.0)
    return float(np.arccos(cosang))

def extract_features(pts):
    from mediapipe.python.solutions.hands import HandLandmark as IDX
    f = {}
    f["thumb_open"] = pair_dist(pts, IDX.THUMB_TIP.value, IDX.THUMB_CMC.value)
    f["idx_open"]   = pair_dist(pts, IDX.INDEX_FINGER_TIP.value, IDX.INDEX_FINGER_MCP.value)
    f["mid_open"]   = pair_dist(pts, IDX.MIDDLE_FINGER_TIP.value, IDX.MIDDLE_FINGER_MCP.value)
    f["ring_open"]  = pair_dist(pts, IDX.RING_FINGER_TIP.value, IDX.RING_FINGER_MCP.value)
    f["pinky_open"] = pair_dist(pts, IDX.PINKY_TIP.value, IDX.PINKY_MCP.value)
    f["thumb_fold"] = angle(IDX.THUMB_CMC.value, IDX.THUMB_MCP.value, IDX.THUMB_IP.value, pts)
    f["idx_fold"]   = angle(IDX.INDEX_FINGER_MCP.value, IDX.INDEX_FINGER_PIP.value, IDX.INDEX_FINGER_DIP.value, pts)
    f["mid_fold"]   = angle(IDX.MIDDLE_FINGER_MCP.value, IDX.MIDDLE_FINGER_PIP.value, IDX.MIDDLE_FINGER_DIP.value, pts)
    f["ring_fold"]  = angle(IDX.RING_FINGER_MCP.value, IDX.RING_FINGER_PIP.value, IDX.RING_FINGER_DIP.value, pts)
    f["pinky_fold"] = angle(IDX.PINKY_MCP.value, IDX.PINKY_PIP.value, IDX.PINKY_DIP.value, pts)
    return f

def predict_letter(landmarks):
    pts = np.array(landmarks, dtype=np.float32)
    feats = extract_features(pts)
    feature_vector = np.array([feats[f] for f in FEATURE_ORDER]).reshape(1, -1)
    feature_vector_scaled = scaler.transform(feature_vector)
    pred = mlp.predict(feature_vector_scaled)[0]
    probs = mlp.predict_proba(feature_vector_scaled)[0]
    confidence = probs[np.where(mlp.classes_ == pred)[0][0]]
    return {"letter": pred, "confidence": float(confidence)}

# -----------------------------
# Endpoint POST /predict
# -----------------------------
@app.post("/predict")
async def predict(data: Landmarks):
    if not data.landmarks:
        return {"letter": None, "confidence": 0.0}
    result = predict_letter(data.landmarks)
    return result

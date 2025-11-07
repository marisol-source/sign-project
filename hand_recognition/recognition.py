# recognition.py
import os
import mediapipe as mp
import numpy as np
import joblib


# ==========================
# Configuración de rutas absolutas
# ==========================
BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, 'modelo_entrenado.pkl')
SCALER_PATH = os.path.join(BASE_DIR, 'scaler.pkl')

# ==========================
# Cargar modelo y escalador
# ==========================
mlp = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

# ==========================
# MediaPipe Hands
# ==========================
mp_hands = mp.solutions.hands
IDX = mp_hands.HandLandmark

# ==========================
# Orden de features (si no usas config, definir aquí)
# ==========================
FEATURE_ORDER = [
    "thumb_open", "idx_open", "mid_open", "ring_open", "pinky_open",
    "thumb_fold", "idx_fold", "mid_fold", "ring_fold", "pinky_fold"
]

# ==========================
# Funciones
# ==========================
def normalize_landmarks(hand_landmarks):
    pts = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark], dtype=np.float32)
    wrist = pts[IDX.WRIST.value, :2]
    pts[:, :2] -= wrist
    ref_vec = pts[IDX.MIDDLE_FINGER_MCP.value, :2]
    ref = np.linalg.norm(ref_vec)
    pts[:, :2] /= ref if ref > 1e-6 else 1.0
    return pts

def pair_dist(pts, a, b):
    pa, pb = pts[a, :2], pts[b, :2]
    return float(np.linalg.norm(pa - pb))

def angle(a, b, c, pts):
    A, B, C = pts[a, :2], pts[b, :2], pts[c, :2]
    BA, BC = A - B, C - B
    denom = (np.linalg.norm(BA) * np.linalg.norm(BC) + 1e-8)
    cosang = np.dot(BA, BC) / denom
    cosang = np.clip(cosang, -1.0, 1.0)
    return float(np.arccos(cosang))

def extract_features(pts):
    f = {}
    f["thumb_open"] = pair_dist(pts, IDX.THUMB_TIP.value, IDX.THUMB_CMC.value)
    f["idx_open"] = pair_dist(pts, IDX.INDEX_FINGER_TIP.value, IDX.INDEX_FINGER_MCP.value)
    f["mid_open"] = pair_dist(pts, IDX.MIDDLE_FINGER_TIP.value, IDX.MIDDLE_FINGER_MCP.value)
    f["ring_open"] = pair_dist(pts, IDX.RING_FINGER_TIP.value, IDX.RING_FINGER_MCP.value)
    f["pinky_open"] = pair_dist(pts, IDX.PINKY_TIP.value, IDX.PINKY_MCP.value)
    f["thumb_fold"] = angle(IDX.THUMB_CMC.value, IDX.THUMB_MCP.value, IDX.THUMB_IP.value, pts)
    f["idx_fold"] = angle(IDX.INDEX_FINGER_MCP.value, IDX.INDEX_FINGER_PIP.value, IDX.INDEX_FINGER_DIP.value, pts)
    f["mid_fold"] = angle(IDX.MIDDLE_FINGER_MCP.value, IDX.MIDDLE_FINGER_PIP.value, IDX.MIDDLE_FINGER_DIP.value, pts)
    f["ring_fold"] = angle(IDX.RING_FINGER_MCP.value, IDX.RING_FINGER_PIP.value, IDX.RING_FINGER_DIP.value, pts)
    f["pinky_fold"] = angle(IDX.PINKY_MCP.value, IDX.PINKY_PIP.value, IDX.PINKY_DIP.value, pts)
    return f

def predict_letter(feats):
    feature_vector = np.array([feats[f] for f in FEATURE_ORDER]).reshape(1, -1)
    feature_vector_scaled = scaler.transform(feature_vector)
    pred = mlp.predict(feature_vector_scaled)[0]
    probabilities = mlp.predict_proba(feature_vector_scaled)[0]
    confidence = probabilities[np.where(mlp.classes_ == pred)[0][0]]
    return pred, confidence

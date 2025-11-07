# hand_api.py
from fastapi import FastAPI
from pydantic import BaseModel
from hand_recognition.recognition import normalize_landmarks, extract_features, predict_letter
from fastapi.middleware.cors import CORSMiddleware
from hand_recognition.correction import corregir_texto_automatico


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LandmarksData(BaseModel):
    landmarks: list  # Coincide con el JSON del frontend

@app.post("/api/test/")
async def predict(data: LandmarksData):
    try:
        # Crear objetos temporales similares a MediaPipe
        class TmpLandmark:
            def __init__(self, x, y, z):
                self.x = x
                self.y = y
                self.z = z
        class TmpHand:
            def __init__(self, landmarks):
                self.landmark = landmarks

        landmarks = [TmpLandmark(**lm) for lm in data.landmarks]
        hand = TmpHand(landmarks)

        pts = normalize_landmarks(hand)
        feats = extract_features(pts)
        letter, confidence = predict_letter(feats)

        return {"letter": letter, "confidence": confidence}
    except Exception as e:
        return {"error": str(e)}


# --------- NUEVO MODELO Y NUEVO ENDPOINT (corrección) ----------
class CorrectionIn(BaseModel):
    sentence: str

class CorrectionOut(BaseModel):
    original: str
    corrected: str

@app.post("/api/correct/", response_model=CorrectionOut)
async def correct_sentence(payload: CorrectionIn):
    original = payload.sentence
    corrected = corregir_texto_automatico(original)
    return {"original": original, "corrected": corrected}

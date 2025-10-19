import os
import joblib

modelo_path = os.path.join(os.path.dirname(__file__), "modelo_entrenado.pkl")
modelo = joblib.load(modelo_path)
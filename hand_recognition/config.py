# config.py

WIN_NAME = 'Reconocimiento de Gestos'
RES_W = 1280
RES_H =  720
PAUSA_LETRA = 1.5
PAUSA_PALABRA = 3.0
VOTE_WINDOW = 7
MIN_STABLE = 5
CONF_THRESH = 0.75
REFRACTORY_MS = 300
NO_HAND_WORD_PAUSE = 0.8
LOW_CONF_PAUSE = 0.8
PAUSA_ORACION = 3.5
PAUSA_TEMPORIZADOR = 5.0  # Pausa de 5 segundos para enviar la oración

FEATURE_ORDER = [
    "thumb_open", "idx_open", "mid_open", "ring_open", "pinky_open",
    "thumb_fold", "idx_fold", "mid_fold", "ring_fold", "pinky_fold"
]

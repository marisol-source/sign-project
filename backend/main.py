import cv2, time, threading
from collections import deque, Counter
from queue import Queue
from ui import setup_tkinter_window, overwrite_text
from reconocimiento.recognition import normalize_landmarks, extract_features, predict_letter
from reconocimiento.correction import corregir_texto_automatico
from reconocimiento.config import *
import warnings
from reconocimiento.utils import polish_text  # Asegúrate de que esto esté al inicio del archivo
import mediapipe as mp
from reconocimiento.voice import manejar_inactividad  # Importamos la función de voz

# Silenciar advertencias de "StandardScaler" si lo deseas
warnings.filterwarnings("ignore", category=UserWarning, message="X does not have valid feature names")

# Inicializamos el motor de pyttsx3 (usado en voice.py)
+------
import pyttsx3
engine = pyttsx3.init()

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
IDX = mp_hands.HandLandmark

data_queue = Queue()
interpretation_active = False

# Variable para controlar la inactividad
last_detection_time = time.time()

def opencv_thread():
    global interpretation_active, texto_original, texto_corregido, last_detection_time
    
    cap = cv2.VideoCapture(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, RES_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RES_H)
    cv2.namedWindow(WIN_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WIN_NAME, RES_W, RES_H)

    vote_queue = deque(maxlen=VOTE_WINDOW)
    confidence_queue = deque(maxlen=VOTE_WINDOW)
    last_accept_time = 0.0
    last_word_time = time.time()
    last_sentence_time = time.time()
    last_commit_char = None
    last_commit_ts = 0.0
    current_word = ""
    texto_original = ""   # Acumula todo el texto original
    texto_corregido = ""  # Acumula todo el texto corregido automáticamente

    no_hand_since = None
    low_conf_since = None

    preferred_hand = "Right"
    last_sent = ("", "", "", "", -1.0)

    with mp_hands.Hands(
        model_complexity=1,
        min_detection_confidence=0.8,
        min_tracking_confidence=0.8,
        max_num_hands=2
    ) as hands:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)
            live_letter = None
            live_confidence = 0.0

            # Selección de mano consistente
            selected_landmarks = None
            if results.multi_hand_landmarks:
                if results.multi_handedness and len(results.multi_hand_landmarks) == len(results.multi_handedness):
                    idx_sel = None
                    for i, handedness in enumerate(results.multi_handedness):
                        label = handedness.classification[0].label
                        if label == preferred_hand:
                            idx_sel = i
                            break
                    if idx_sel is None:
                        idx_sel = 0
                    selected_landmarks = results.multi_hand_landmarks[idx_sel]
                else:
                    selected_landmarks = results.multi_hand_landmarks[0]

            if selected_landmarks is not None:
                mp_drawing.draw_landmarks(frame, selected_landmarks, mp_hands.HAND_CONNECTIONS)

            # Lógica principal
            if interpretation_active and selected_landmarks is not None:
                pts = normalize_landmarks(selected_landmarks)
                feats = extract_features(pts)
                raw_letter, raw_confidence = predict_letter(feats)

                vote_queue.append(raw_letter)
                confidence_queue.append(raw_confidence)

                counts = Counter(vote_queue)
                stable_letter, times = counts.most_common(1)[0]

                confidences = [confidence_queue[i] for i, letter in enumerate(vote_queue) if letter == stable_letter]
                avg_confidence = (sum(confidences) / len(confidences)) if confidences else 0.0

                if avg_confidence >= CONF_THRESH:
                    live_letter = stable_letter
                    live_confidence = avg_confidence
                else:
                    live_letter = None
                    live_confidence = avg_confidence

                now = time.time()

                if times >= MIN_STABLE and avg_confidence >= CONF_THRESH and (now - last_accept_time) >= PAUSA_LETRA:
                    if not (stable_letter == last_commit_char and (now - last_commit_ts) < (REFRACTORY_MS/1000.0)):
                        current_word += stable_letter
                        last_commit_char = stable_letter
                        last_commit_ts = now
                        last_accept_time = now
                        last_word_time = now
                        last_sentence_time = now
                        vote_queue.clear()
                        confidence_queue.clear()

                # Reset de timers
                no_hand_since = None
                if avg_confidence >= CONF_THRESH:
                    low_conf_since = None
                else:
                    if low_conf_since is None:
                        low_conf_since = now

            # Cierre de palabra por reglas
            now = time.time()
            if interpretation_active and selected_landmarks is None:
                if no_hand_since is None:
                    no_hand_since = now

            should_close_word = False
            if interpretation_active and current_word:
                if (now - last_word_time) > PAUSA_PALABRA:
                    should_close_word = True
                if no_hand_since is not None and (now - no_hand_since) >= NO_HAND_WORD_PAUSE:
                    should_close_word = True
                if low_conf_since is not None and (now - low_conf_since) >= LOW_CONF_PAUSE:
                    should_close_word = True

            if should_close_word:
                texto_original += current_word + " "
                texto_corregido = corregir_texto_automatico(texto_original)  # Corrección con LanguageTool y capitalización

                current_word = ""
                last_commit_char = None
                last_commit_ts = 0.0
                last_word_time = now
                last_sentence_time = now
                vote_queue.clear()
                confidence_queue.clear()
                no_hand_since = None
                low_conf_since = None

            # Cierre de oración por pausa larga
            should_close_sentence = False
            if interpretation_active and not current_word and texto_original.strip():
                if (now - last_sentence_time) >= PAUSA_TEMPORIZADOR:
                    should_close_sentence = True

            if should_close_sentence:
                if not texto_original.strip().endswith((".", "!", "?")):
                    texto_original = texto_original.strip() + ". "
                    texto_corregido = corregir_texto_automatico(texto_original)
                last_sentence_time = now

            # Overlay
            status_text = "Interpretando (I para pausar)" if interpretation_active else "Presiona 'I' para comenzar"
            cv2.putText(frame, status_text, (12, 36),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (209, 199, 0) if interpretation_active else (0, 0, 255), 2, cv2.LINE_AA)

            if interpretation_active:
                if live_letter:
                    confidence_text = f"{live_letter} P: ({live_confidence*100:.1f}%)"
                else:
                    confidence_text = "-"

                cv2.putText(frame, f'Live: {confidence_text}', (12, 72),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (240, 228, 0), 1, cv2.LINE_AA)

                word_preview = current_word if current_word else "-"
                cv2.putText(frame, f'Word: {word_preview}', (12, 108),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 245, 46), 1, cv2.LINE_AA)

            cv2.imshow(WIN_NAME, frame)

            # Enviar a Tkinter solo si hay cambios
            if interpretation_active or texto_original or texto_corregido:
                packet = (texto_original, texto_corregido, current_word, (live_letter or ""), float(live_confidence))
                if packet != last_sent:
                    data_queue.put(packet)
                    last_sent = packet

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('i'):
                # Toggle iniciar/pausar
                interpretation_active = not interpretation_active
                vote_queue.clear()
                confidence_queue.clear()
                if interpretation_active:
                    last_accept_time = time.time()
                    last_word_time = time.time()
                    last_sentence_time = time.time()
                    data_queue.put(("", "", "", "", 0.0))
            elif key == ord('r'):  # Tecla R para borrar oración
                texto_original = ""
                texto_corregido = ""
                current_word = ""
                last_word_time = time.time()
                last_sentence_time = time.time()
                vote_queue.clear()
                confidence_queue.clear()
                data_queue.put(("", "", "", "", 0.0))
                print(">>> Oración borrada por tecla R")

    cap.release()
    cv2.destroyAllWindows()
    data_queue.put(None)

def update_tkinter():
    last_data = None
    while True:
        try:
            data = data_queue.get_nowait()
            if data is None:
                root.quit()
                return
            last_data = data
        except:
            break
            
    if last_data is not None:
        original_text, fixed_text, current_word, live_letter, live_confidence = last_data
        overwrite_text(text_area, original_text, fixed_text, current_word, live_letter, live_confidence)
        
    root.after(15, update_tkinter)

root, text_area = setup_tkinter_window()

# Iniciar hilo de OpenCV
thread = threading.Thread(target=opencv_thread, daemon=True)
thread.start()

# Actualizar Tkinter periódicamente
root.after(50, update_tkinter)

# Manejar cierre de ventana
def on_closing():
    cv2.destroyAllWindows()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()

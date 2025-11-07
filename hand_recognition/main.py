import cv2, time, threading
from collections import deque, Counter
from queue import Queue
from ui import setup_tkinter_window, overwrite_text
from hand_recognition.recognition import normalize_landmarks, extract_features, predict_letter
from correction import corregir_texto_automatico
from config import *
import warnings
from utils import polish_text
import mediapipe as mp

# Silenciar advertencias
warnings.filterwarnings("ignore", category=UserWarning, message="X does not have valid feature names")

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
IDX = mp_hands.HandLandmark

data_queue = Queue()
interpretation_active = False

# Variables globales para corrección
correction_in_progress = False
texto_original_global = ""
texto_corregido_global = ""
last_correction_time = 0  # Para prevenir correcciones demasiado seguidas

def opencv_thread():
    global interpretation_active, correction_in_progress, texto_original_global, texto_corregido_global, last_correction_time
    
    cap = cv2.VideoCapture(2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, RES_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RES_H)
    cv2.namedWindow(WIN_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WIN_NAME, RES_W, RES_H)

    vote_queue = deque(maxlen=VOTE_WINDOW)
    confidence_queue = deque(maxlen=VOTE_WINDOW)
    last_accept_time = 0.0
    last_commit_char = None
    last_commit_ts = 0.0
    current_word = ""
    texto_original = ""   # Acumula todo el texto original
    texto_corregido = ""  # Acumula todo el texto corregido automáticamente

    # TEMPORIZADORES CLAVE
    last_letter_time = time.time()  # Para palabra (3 segundos)
    last_activity_time = time.time()  # Para interpretación (5 segundos)
    
    # CONSTANTES DE TEMPORIZADORES
    INTERPRETATION_TIMEOUT = 5.0  # 5 segundos para enviar a interpretación
    MIN_CORRECTION_INTERVAL = 10.0  # Mínimo 10 segundos entre correcciones

    preferred_hand = "Right"
    last_sent = ("", "", "", "", -1.0)

    # Variable para controlar si ya se envió una corrección
    pending_correction = False

    def run_correction(text_to_correct):
        """Ejecuta la corrección y actualiza las variables globales"""
        global correction_in_progress, texto_corregido_global, texto_original_global, last_correction_time
        
        try:
            print(f"🔧 Iniciando corrección Gemini para: '{text_to_correct}'")
            corrected = corregir_texto_automatico(text_to_correct)
            texto_corregido_global = corrected   # ORACION CORREGIDA
            texto_original_global = text_to_correct  # ORACION ORIGINAL
            print(f"✅ Corrección completada: '{corrected}'")
        except Exception as e:
            print(f"❌ Error en corrección: {e}")
            texto_corregido_global = text_to_correct  # Fallback al texto original
        finally:
            correction_in_progress = False
            last_correction_time = time.time()

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

            # Lógica principal de reconocimiento
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
                        # ACTUALIZAR AMBOS TEMPORIZADORES
                        last_letter_time = now
                        last_activity_time = now
                        vote_queue.clear()
                        confidence_queue.clear()
                        print(f"📝 Letra agregada: {stable_letter} - Palabra actual: {current_word}")
                        # Resetear la bandera de corrección pendiente cuando hay nueva actividad
                        pending_correction = False

            # LÓGICA DE TEMPORIZADORES
            now = time.time()
            time_since_last_letter = now - last_letter_time
            time_since_last_activity = now - last_activity_time
            time_since_last_correction = now - last_correction_time

            # TEMPORIZADOR DE PALABRA (3 segundos)
            if (interpretation_active and 
                current_word and 
                time_since_last_letter >= PAUSA_PALABRA):
                
                # Cerrar palabra actual y agregar espacio
                texto_original += current_word + " "
                print(f"⏰ Palabra cerrada después de {time_since_last_letter:.1f}s: '{current_word}'")
                print(f"📄 Texto acumulado: {texto_original}")
                
                # Reiniciar para nueva palabra
                current_word = ""
                last_commit_char = None
                last_commit_ts = 0.0
                vote_queue.clear()
                confidence_queue.clear()

            # TEMPORIZADOR DE INTERPRETACIÓN (5 segundos) - CORREGIDO
            if (interpretation_active and 
                not correction_in_progress and
                not pending_correction and  # Evitar múltiples correcciones
                time_since_last_activity >= INTERPRETATION_TIMEOUT and 
                time_since_last_correction >= MIN_CORRECTION_INTERVAL and  # Prevenir correcciones seguidas
                texto_original.strip()):
                
                print(f"🚀 Enviando a interpretación después de {time_since_last_activity:.1f}s de inactividad")
                print(f"📤 Texto a interpretar: '{texto_original.strip()}'")
                
                # Marcar que hay una corrección pendiente
                pending_correction = True
                
                # Iniciar corrección en hilo separado
                correction_in_progress = True
                correction_thread = threading.Thread(
                    target=run_correction, 
                    args=(texto_original.strip(),),
                    daemon=True
                )
                correction_thread.start()
                
                # Reiniciar temporizador de interpretación
                last_activity_time = now

            # Actualizar texto corregido si hay uno nuevo disponible
            if texto_corregido_global and not correction_in_progress:
                texto_corregido = texto_corregido_global
                # Limpiar para evitar repeticiones
                texto_corregido_global = ""
                # Reiniciar el texto original después de la corrección para evitar repeticiones
                texto_original = ""
                pending_correction = False
                print("🔄 Texto reiniciado después de corrección")

            # Overlay con información de temporizadores
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
                
                # Mostrar temporizadores y estado de corrección
                word_time_left = max(0, PAUSA_PALABRA - time_since_last_letter) if current_word else 0
                interpretation_time_left = max(0, INTERPRETATION_TIMEOUT - time_since_last_activity)
                
                # Temporizador de palabra (solo si hay palabra en progreso)
                if current_word:
                    word_timer_text = f"Palabra: {word_time_left:.1f}s"
                    cv2.putText(frame, word_timer_text, (12, 144),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
                
                # Temporizador de interpretación (siempre)
                interpretation_timer_text = f"Interpretación: {interpretation_time_left:.1f}s"
                color = (255, 165, 0) if interpretation_time_left > 1.0 else (0, 0, 255)
                cv2.putText(frame, interpretation_timer_text, (12, 168 if current_word else 144),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1, cv2.LINE_AA)
                
                # Estado de corrección
                correction_status = "Corrigiendo..." if correction_in_progress else "Listo"
                status_color = (0, 255, 255) if correction_in_progress else (0, 255, 0)
                cv2.putText(frame, f"Estado: {correction_status}", (12, 192),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 1, cv2.LINE_AA)

            cv2.imshow(WIN_NAME, frame)

            # Enviar a Tkinter - usar variables globales para texto corregido
            display_corrected = texto_corregido_global if correction_in_progress else texto_corregido
            if interpretation_active or texto_original or display_corrected:
                packet = (texto_original, display_corrected, current_word, (live_letter or ""), float(live_confidence))
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
                    # REINICIAR AMBOS TEMPORIZADORES
                    last_letter_time = time.time()
                    last_activity_time = time.time()
                    data_queue.put(("", "", "", "", 0.0))
                    print(">>> Interpretación ACTIVADA")
                else:
                    print(">>> Interpretación PAUSADA")
            elif key == ord('r'):  # Tecla R para borrar oración
                texto_original = ""
                texto_corregido = ""
                texto_corregido_global = ""
                texto_original_global = ""
                current_word = ""
                correction_in_progress = False
                pending_correction = False
                last_correction_time = 0
                # REINICIAR AMBOS TEMPORIZADORES
                last_letter_time = time.time()
                last_activity_time = time.time()
                vote_queue.clear()
                confidence_queue.clear()
                data_queue.put(("", "", "", "", 0.0))
                print(">>> Oración borrada por tecla R")
            elif key == ord('t'):  # Tecla T para TEST de Gemini
                if texto_original.strip() and not correction_in_progress and not pending_correction:
                    print("🧪 TEST: Forzando corrección con tecla T")
                    pending_correction = True
                    correction_in_progress = True
                    correction_thread = threading.Thread(
                        target=run_correction, 
                        args=(texto_original.strip(),),
                        daemon=True
                    )
                    correction_thread.start()

    cap.release()
    cv2.destroyAllWindows()
    data_queue.put(None)

def update_tkinter():
    last_data = None
    processed_count = 0
    max_process_per_cycle = 10
    
    while processed_count < max_process_per_cycle:
        try:
            data = data_queue.get_nowait()
            if data is None:
                root.quit()
                return
            last_data = data
            processed_count += 1
        except:
            break
            
    if last_data is not None:
        try:
            original_text, fixed_text, current_word, live_letter, live_confidence = last_data
            overwrite_text(text_area, original_text, fixed_text, current_word, live_letter, live_confidence)
        except Exception as e:
            print(f"Error actualizando UI: {e}")
        
    root.after(20, update_tkinter)

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
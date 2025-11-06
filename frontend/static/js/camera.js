// Ubicación:: static/app/js/camera.js
// Versión con logs y manejo de errores. Expone window.startCamera(hands).

(function () {
  // -------------------------
  // CONFIG
  // -------------------------
  const CONFIG = {
    RES_W: 1280,                // Ancho de la cámara (en píxeles)
    RES_H: 720,                 // Alto de la cámara (en píxeles)
    PAUSA_LETRA: 1.5,           // Espera 1.5 segundos antes de aceptar una nueva letra
    PAUSA_PALABRA: 3.0,         // Si no hay movimiento durante 3 segundos, se asume el fin de una palabra
    PAUSA_ORACION: 3.5,         // Pausa más larga, para separar oraciones completas
    PAUSA_TEMPORIZADOR: 5.0,    // Tiempo máximo antes de reiniciar el temporizador o limpiar el buffer
    CONF_THRESH: 0.75,          // Umbral de confianza mínimo para aceptar una predicción
    BUFFER_SIZE: 5,             // Número de muestras almacenadas para suavizar las predicciones
    MIN_CONFIDENCE: 0.5,        // Nivel mínimo de confianza global para procesar un cuadro del video
    API_INTERVAL: 250           // Intervalo (en milisegundos) para enviar datos o actualizaciones a la API
  };






  // -------------------------
  // Elementos DOM (se asume que existen en el HTML)
  // -------------------------
  const video = document.getElementById('input_video');
  const canvas = document.getElementById('output_canvas');
  const ctx = canvas ? canvas.getContext('2d') : null;
  const estado = document.getElementById('estado');
  const barra = document.getElementById('barra');
  const timerValue = document.getElementById('timerValue');
  const chat = document.getElementById('chat');

  // Variables de estado
  let lastGestureTime = Date.now();
  let lastDetected = false;
  let currentTimer = 0;
  let cameraOn = true;
  let paused = false;
  let cameraInstance = null;
  let bufferLetras = [];
  let ultimaLetra = null;
  let lastApiCall = 0;
  let apiInProgress = false;

  // -------------------------
  // Logs iniciales
  // -------------------------
  console.log('[camera.js] cargado');

 // -------------------------
  // Funciones cámara
  // -------------------------
  async function setupCamera() {
    try {
      console.log('[camera.js] solicitando getUserMedia...');
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: CONFIG.RES_W, height: CONFIG.RES_H, facingMode: 'user' },
        audio: false
      });
      video.srcObject = stream;
      await video.play();
      console.log('[camera.js] cámara inicializada correctamente');
      cameraOn = true;
      if (estado) estado.textContent = '📸 Cámara encendida';
      return stream;
    } catch (err) {
      console.error('[camera.js] Error al acceder a la cámara:', err);
      if (estado) estado.textContent = '❌ Error cámara';
      throw err;
    }
  }

  async function startCamera(hands) {
    try {
      if (!video) throw new Error('video element no encontrado');
      if (!hands) console.warn('[camera.js] startCamera: no se recibió objeto "hands".');

      // Espera a que el video cargue
      if (video.readyState < 1) {
        await new Promise(res => video.addEventListener('loadeddata', res, { once: true }));
      }

      // Preparar canvas
      if (canvas) {
        canvas.width = CONFIG.RES_W;
        canvas.height = CONFIG.RES_H;
      }

      // Inicializa getUserMedia
      await setupCamera();

      // Si MediaPipe Camera no existe, fallback a loop manual
      if (typeof Camera === 'undefined') {
        console.warn('[camera.js] Camera no definida, usando fallback con requestAnimationFrame');
        const loop = async () => {
          if (!video.paused && !video.ended) {
            if (hands && typeof hands.send === 'function') {
              try { await hands.send({ image: video }); } catch {}
            }
            requestAnimationFrame(loop);
          }
        };
        requestAnimationFrame(loop);
        return;
      }

      // Inicializa MediaPipe Camera
      cameraInstance = new Camera(video, {
        onFrame: async () => {
          try {
            if (hands && typeof hands.send === 'function') await hands.send({ image: video });
          } catch (err) {
            console.error('[camera.js] Error en onFrame -> hands.send:', err);
          }
        },
        width: CONFIG.RES_W,
        height: CONFIG.RES_H
      });
      cameraInstance.start();
      console.log('[camera.js] cameraInstance iniciada');
    } catch (err) {
      console.error('[camera.js] startCamera fallo:', err);
      if (estado) estado.textContent = '❌ Error cámara';
    }
  }

  // -------------------------
  // Botones
  // -------------------------
  function attachButtonListeners() {
    const btnCam = document.getElementById('btnCam');
    const btnPause = document.getElementById('btnPause');
    const btnReset = document.getElementById('btnReset');
    const btnStop = document.getElementById('btnStop');

    if (btnCam) {
      btnCam.addEventListener('click', async () => {
        try {
          if (cameraOn) {
            // Detener cámara
            if (cameraInstance && typeof cameraInstance.stop === 'function') cameraInstance.stop();
            if (video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
            video.srcObject = null;
            cameraOn = false;
            if (estado) estado.textContent = '📷 Cámara apagada';
            console.log('[camera.js] cámara apagada por usuario.');
          } else {
            // Reiniciar startCamera correctamente
            if (window.handsInstance) {
              await startCamera(window.handsInstance);
            } else {
              console.warn('[camera.js] No hay handsInstance definido para reiniciar cámara');
            }
          }
        } catch (err) {
          console.error('[camera.js] Error toggle cam:', err);
        }
      });
    }

    if (btnPause) btnPause.addEventListener('click', () => {
      paused = !paused;
      if (estado) estado.textContent = paused ? '⏸️ Pausado' : '▶️ Reanudado';
      console.log('[camera.js] paused ->', paused);
    });

    if (btnReset) btnReset.addEventListener('click', () => {
      lastDetected = false;
      currentTimer = 0;
      if (barra) barra.style.width = '0%';
      if (timerValue) timerValue.textContent = '0.0';
      if (estado) estado.textContent = '🔄 Reiniciado';
      bufferLetras = [];
      ultimaLetra = null;
      if (chat) chat.innerHTML = '';
      console.log('[camera.js] estado reiniciado');
    });

    if (btnStop) btnStop.addEventListener('click', () => {
      try {
        if (cameraInstance && typeof cameraInstance.stop === 'function') cameraInstance.stop();
        if (video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
        if (estado) estado.textContent = '🛑 Reconocimiento terminado';
        console.log('[camera.js] stop pulsado');
        cameraOn = false;
      } catch (err) {
        console.error('[camera.js] Error al detener:', err);
      }
    });
  }

  // -------------------------
  // Inicialización
  // -------------------------
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', attachButtonListeners);
  } else {
    attachButtonListeners();
  }

  // Inicia cámara automáticamente si hay handsInstance
  document.addEventListener('DOMContentLoaded', async () => {
    if (window.handsInstance) {
      await startCamera(window.handsInstance);
    } else {
      console.log('[camera.js] handsInstance no definido, no se inicia cámara automáticamente');
    }
  });

  // Exponer startCamera y debug
  window.startCamera = startCamera;
  window._CAMERA_JS = {
    startCamera,
    CONFIG,
    getState: () => ({ cameraOn, paused, cameraInstanceExists: !!cameraInstance })
  };

  console.log('[camera.js] listo. Llama a startCamera(hands) desde tu HTML.');
})();




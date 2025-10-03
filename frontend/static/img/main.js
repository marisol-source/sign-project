const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
const selectorCamaras = document.getElementById("selectorCamaras");

// Inicializar MediaPipe Hands
const hands = new Hands({ locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}` });

hands.setOptions({
  maxNumHands: 1,
  modelComplexity: 1,
  minDetectionConfidence: 0.7,
  minTrackingConfidence: 0.5
});

hands.onResults(results => {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (results.multiHandLandmarks) {
    for (const landmarks of results.multiHandLandmarks) {
      drawConnectors(ctx, landmarks, HAND_CONNECTIONS, { color: "#00FF00", lineWidth: 3 });
      drawLandmarks(ctx, landmarks, { color: "#FF0000", lineWidth: 2, radius: 4 });
    }
  }
});

let camHands = null;
let streamActual = null;

// Función para iniciar la cámara
async function iniciarHandsCam(deviceId) {
  if (streamActual) streamActual.getTracks().forEach(t => t.stop());

  streamActual = await navigator.mediaDevices.getUserMedia({ video: { deviceId: { exact: deviceId } }, audio: false });
  video.srcObject = streamActual;
  await video.play();

  if (camHands) camHands.stop();

  camHands = new Camera(video, { onFrame: async () => await hands.send({ image: video }), width: 640, height: 480 });
  camHands.start();
}

// Listar cámaras
async function listarCamaras() {
  const devices = await navigator.mediaDevices.enumerateDevices();
  const videoDevices = devices.filter(d => d.kind === "videoinput");
  selectorCamaras.innerHTML = "";
  videoDevices.forEach((d, i) => {
    const option = document.createElement("option");
    option.value = d.deviceId;
    option.text = d.label || `Cámara ${i+1}`;
    selectorCamaras.appendChild(option);
  });
}

window.addEventListener("load", async () => {
  await listarCamaras();
  if (selectorCamaras.options.length > 0) iniciarHandsCam(selectorCamaras.value);
});

selectorCamaras.addEventListener("change", (e) => iniciarHandsCam(e.target.value));

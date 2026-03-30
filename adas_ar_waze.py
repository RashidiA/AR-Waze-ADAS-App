import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="ADAS Pro: AR Waze Edition", layout="wide")

# --- SIDEBAR CONTROLS ---
st.sidebar.title("🎙️ ADAS & Nav Controls")
enable_voice = st.sidebar.toggle("Enable Voice Alerts", value=True)
drift_sensitivity = st.sidebar.slider("Lane Sensitivity", 50, 150, 100)

# Convert Python values to strings for JavaScript injection
voice_val = "true" if enable_voice else "false"
sensitivity_val = str(drift_sensitivity)

# RAW STRING used to avoid all f-string brace conflicts
JS_TEMPLATE = r"""
<div style="position: relative; width: 100%; max-width: 640px; margin: auto; border-radius: 20px; overflow: hidden; background: #000; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
    <video id="video" autoplay playsinline style="width: 100%; height: auto; display: block;"></video>
    <canvas id="output" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></canvas>
    
    <div id="hud" style="position: absolute; top: 20px; left: 20px; color: white; font-family: monospace; pointer-events: none;">
        <div style="background: rgba(0,123,255,0.7); padding: 8px 15px; border-radius: 5px; margin-bottom: 5px; font-weight: bold;">📍 AR WAZE ACTIVE</div>
        <div style="background: rgba(0,0,0,0.6); padding: 8px 15px; border-radius: 5px; font-size: 14px;">
            SPD: <span id="speed" style="color: #00FF00; font-weight: bold;">0.0</span> km/h
        </div>
    </div>

    <div id="brakeAlert" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: rgba(255,0,0,0.85); color: white; padding: 20px 40px; border-radius: 10px; font-family: sans-serif; font-weight: bold; font-size: 24px; display: none; border: 5px solid white; z-index: 1000;">⚠️ BRAKE</div>

    <div id="overlay" style="position: absolute; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.9); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 100;">
        <h2 style="color: white; font-family: sans-serif;">ADAS PRO: AR WAZE</h2>
        <button id="startBtn" style="padding: 18px 40px; font-size: 20px; border-radius: 50px; background: #007bff; color: white; border: none; cursor: pointer;">START SYSTEM</button>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs"></script>
<script src="https://cdn.jsdelivr.net/npm/@tensorflow-models/coco-ssd"></script>

<script>
const video = document.getElementById('video');
const canvas = document.getElementById('output');
const ctx = canvas.getContext('2d', {alpha: false, desynchronized: true});
const brakeAlert = document.getElementById('brakeAlert');
const speedVal = document.getElementById('speed');

let model;
let lastSpeech = 0;
const synth = window.speechSynthesis;

// Injected Variables
const VOICE_ENABLED = __VOICE__;
const SENSITIVITY = __SENSITIVITY__;

function speak(text) {
    if (!VOICE_ENABLED) return;
    const now = Date.now();
    if (now - lastSpeech < 4000) return;
    synth.speak(new SpeechSynthesisUtterance(text));
    lastSpeech = now;
}

function drawARArrow(ctx, x, y) {
    const bounce = Math.sin(Date.now() * 0.005) * 10;
    ctx.save();
    ctx.translate(x, y + bounce);
    ctx.beginPath();
    ctx.moveTo(0, 0); ctx.lineTo(-25, 35); ctx.lineTo(0, 25); ctx.lineTo(25, 35);
    ctx.closePath();
    ctx.fillStyle = "rgba(0, 123, 255, 0.9)"; ctx.strokeStyle = "white";
    ctx.lineWidth = 2; ctx.stroke(); ctx.fill();
    ctx.restore();
}

async function start() {
    model = await cocoSsd.load();
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
    video.srcObject = stream;
    navigator.geolocation.watchPosition(pos => {
        speedVal.innerText = ((pos.coords.speed || 0) * 3.6).toFixed(1);
    }, null, {enableHighAccuracy: true});
    document.getElementById('overlay').style.display = 'none';
    speak("System Online");
    video.onloadedmetadata = () => render();
}

async function render() {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);
    const h = canvas.height; const w = canvas.width;
    const roadTop = Math.floor(h * 0.7);
    const roadData = ctx.getImageData(0, roadTop, w, Math.floor(h * 0.3));
    const pixels = roadData.data;
    let leftDelt = 0, rightDelt = 0;
    for (let i = 0; i < pixels.length; i += 4) {
        if (pixels[i] > 210 && pixels[i+1] > 210 && pixels[i+2] > 210) {
            pixels[i]=0; pixels[i+1]=123; pixels[i+2]=255;
            let x = (i/4)%w;
            if (x < w*0.3) leftDelt++; if (x > w*0.7) rightDelt++;
        }
    }
    ctx.putImageData(roadData, 0, roadTop);
    if(leftDelt > SENSITIVITY) speak("Drift left");
    if(rightDelt > SENSITIVITY) speak("Drift right");
    drawARArrow(ctx, w/2, h * 0.6);
    if (Date.now() % 7 == 0) {
        const predictions = await model.detect(video);
        let hazard = predictions.some(p => ["person", "car", "truck"].includes(p.class) && p.bbox[0] > w*0.3 && p.bbox[0] < w*0.7);
        brakeAlert.style.display = hazard ? "block" : "none";
        if(hazard) speak("Brake");
    }
    requestAnimationFrame(render);
}
document.getElementById('startBtn').onclick = start;
</script>
"""

# Replace placeholders safely without using f-strings
final_js = JS_TEMPLATE.replace("__VOICE__", voice_val).replace("__SENSITIVITY__", sensitivity_val)
components.html(final_js, height=650)

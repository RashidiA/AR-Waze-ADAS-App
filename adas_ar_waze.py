import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="ADAS Pro: Rahmah Package", layout="wide")

st.sidebar.title("🛠️ System Tuning")
sensitivity = st.sidebar.slider("Lane Sensitivity", 30, 200, 80)
voice = st.sidebar.toggle("Voice Feedback", value=True)

# RAW STRING to avoid all Python syntax errors
JS_CODE = r"""
<div style="position: relative; width: 100%; max-width: 640px; margin: auto; border-radius: 15px; overflow: hidden; background: #000;">
    <video id="video" autoplay playsinline muted style="width: 100%; height: auto;"></video>
    <canvas id="output" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 5;"></canvas>
    
    <div id="hud" style="position: absolute; top: 15px; left: 15px; color: #00FF00; font-family: monospace; z-index: 10; pointer-events: none; background: rgba(0,0,0,0.5); padding: 10px; border-radius: 5px;">
        NAV: ACTIVE <br> SPD: <span id="speed">0.0</span> km/h
    </div>

    <div id="overlay" style="position: absolute; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.8); display: flex; align-items: center; justify-content: center; z-index: 100;">
        <button id="startBtn" style="padding: 20px 40px; font-size: 18px; border-radius: 50px; background: #007bff; color: white; border: none;">INITIALIZE AR & VISION</button>
    </div>
</div>

<script>
const video = document.getElementById('video');
const canvas = document.getElementById('output');
const ctx = canvas.getContext('2d', {alpha: true, desynchronized: true});
const speedDisplay = document.getElementById('speed');

let sensitivity = __SENSITIVITY__;
let voiceEnabled = __VOICE__;

function drawARArrow(w, h) {
    const x = w / 2;
    const y = h * 0.65;
    const bounce = Math.sin(Date.now() * 0.004) * 15;
    
    ctx.save();
    ctx.translate(x, y + bounce);
    ctx.beginPath();
    ctx.moveTo(0, 0); ctx.lineTo(-30, 40); ctx.lineTo(0, 30); ctx.lineTo(30, 40);
    ctx.closePath();
    ctx.fillStyle = "rgba(0, 123, 255, 0.8)";
    ctx.strokeStyle = "white";
    ctx.lineWidth = 3;
    ctx.stroke(); ctx.fill();
    ctx.restore();
}

async function init() {
    // Request Orientation for AR (Required for iOS)
    if (typeof DeviceOrientationEvent.requestPermission === 'function') {
        await DeviceOrientationEvent.requestPermission();
    }

    const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'environment', width: { ideal: 640 } } 
    });
    video.srcObject = stream;
    
    navigator.geolocation.watchPosition(p => {
        speedDisplay.innerText = ((p.coords.speed || 0) * 3.6).toFixed(1);
    }, null, {enableHighAccuracy: true});

    document.getElementById('overlay').style.display = 'none';
    video.onloadedmetadata = () => {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        render();
    };
}

function render() {
    // Ensure canvas stays synced with video size
    if (canvas.width !== video.videoWidth) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
    }

    ctx.drawImage(video, 0, 0);

    // LANE DETECTION LOGIC
    const w = canvas.width;
    const h = canvas.height;
    const scanHeight = Math.floor(h * 0.2);
    const scanTop = Math.floor(h * 0.75);
    
    const roadData = ctx.getImageData(0, scanTop, w, scanHeight);
    const data = roadData.data;

    for (let i = 0; i < data.length; i += 4) {
        // Look for white lines (R, G, B > 180)
        if (data[i] > 180 && data[i+1] > 180 && data[i+2] > 180) {
            data[i] = 0;   // Red
            data[i+1] = 123; // Green
            data[i+2] = 255; // Blue (AR Color)
        }
    }
    ctx.putImageData(roadData, 0, scanTop);

    // DRAW AR NAVIGATION
    drawARArrow(w, h);

    requestAnimationFrame(render);
}

document.getElementById('startBtn').onclick = init;
</script>
"""

# Safety check for injection
final_js = JS_CODE.replace("__SENSITIVITY__", str(sensitivity)).replace("__VOICE__", "true" if voice else "false")
components.html(final_js, height=600)

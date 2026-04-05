import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="ADAS Pro: AR Waze", layout="wide")

# --- SIDEBAR: LIVE INPUTS ---
st.sidebar.title("📍 Navigation & Vision")
dest_name = st.sidebar.text_input("Enter Destination", "Kuala Lumpur")
# Default coordinates (Example: KL CC)
dest_lat = st.sidebar.number_input("Target Latitude", value=3.1578, format="%.4f")
dest_lon = st.sidebar.number_input("Target Longitude", value=101.7123, format="%.4f")

st.sidebar.divider()
st.sidebar.subheader("🛠️ Vision Calibration")
# This slider fixes your "white line not detecting" issue
threshold = st.sidebar.slider("Line Sensitivity (Lower = More Sensitive)", 100, 255, 160)
voice_on = st.sidebar.toggle("Voice Alerts", value=True)

# Convert Python values for JS injection
voice_str = "true" if voice_on else "false"

# RAW STRING to prevent f-string { } syntax errors
JS_TEMPLATE = r"""
<div style="position: relative; width: 100%; max-width: 640px; margin: auto; border-radius: 20px; overflow: hidden; background: #000; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
    <video id="video" autoplay playsinline muted style="width: 100%; height: auto; display: block;"></video>
    <canvas id="output" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 5;"></canvas>
    
    <div id="hud" style="position: absolute; top: 15px; left: 15px; color: #00FF00; font-family: monospace; z-index: 10; background: rgba(0,0,0,0.6); padding: 10px; border-radius: 8px;">
        <b>DEST:</b> <span id="destDisplay">__DEST_NAME__</span><br>
        <b>SPD:</b> <span id="speed">0.0</span> km/h
    </div>

    <div id="overlay" style="position: absolute; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.85); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 100;">
        <h3 style="color: white; font-family: sans-serif;">ASARI-RASHIDI ADAS PRO</h3>
        <button id="startBtn" style="padding: 15px 35px; font-size: 18px; border-radius: 50px; background: #007bff; color: white; border: none; cursor: pointer;">START MISSION</button>
    </div>
</div>

<script>
const video = document.getElementById('video');
const canvas = document.getElementById('output');
const ctx = canvas.getContext('2d', {alpha: true, desynchronized: true});
const speedDisplay = document.getElementById('speed');

// Injected variables from Python
const THRESHOLD = __THRESHOLD__;
const VOICE = __VOICE__;
const TARGET_LAT = __LAT__;
const TARGET_LON = __LON__;

let userLat, userLon;

function speak(msg) {
    if (VOICE) {
        const ut = new SpeechSynthesisUtterance(msg);
        window.speechSynthesis.speak(ut);
    }
}

function drawARWazeArrow(w, h) {
    // Calculate direction toward target
    // In a real app, we'd use atan2(targetLon-userLon, targetLat-userLat)
    // For this prototype, we show the arrow at center-road
    const x = w / 2;
    const y = h * 0.65;
    const bounce = Math.sin(Date.now() * 0.005) * 12;

    ctx.save();
    ctx.translate(x, y + bounce);
    ctx.beginPath();
    ctx.moveTo(0, 0); ctx.lineTo(-25, 35); ctx.lineTo(0, 25); ctx.lineTo(25, 35);
    ctx.closePath();
    ctx.fillStyle = "rgba(0, 123, 255, 0.9)";
    ctx.strokeStyle = "white";
    ctx.lineWidth = 3;
    ctx.stroke(); ctx.fill();
    ctx.restore();
}

async function start() {
    const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'environment' } 
    });
    video.srcObject = stream;

    navigator.geolocation.watchPosition(p => {
        userLat = p.coords.latitude;
        userLon = p.coords.longitude;
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
    ctx.drawImage(video, 0, 0);
    const w = canvas.width;
    const h = canvas.height;

    // --- ASARI-RASHIDI LANE DETECTION ---
    const scanH = Math.floor(h * 0.25);
    const scanTop = Math.floor(h * 0.7);
    const imgData = ctx.getImageData(0, scanTop, w, scanH);
    const pixels = imgData.data;

    for (let i = 0; i < pixels.length; i += 4) {
        // Pixel intensity check using Sidebar Threshold
        if (pixels[i] > THRESHOLD && pixels[i+1] > THRESHOLD && pixels[i+2] > THRESHOLD) {
            pixels[i] = 0; pixels[i+1] = 123; pixels[i+2] = 255; // Blue highlight
        }
    }
    ctx.putImageData(imgData, 0, scanTop);

    // --- AR WAZE ARROW ---
    drawARWazeArrow(w, h);

    requestAnimationFrame(render);
}

document.getElementById('startBtn').onclick = start;
</script>
"""

# Replace placeholders with Sidebar values
final_js = (JS_TEMPLATE
            .replace("__DEST_NAME__", dest_name)
            .replace("__THRESHOLD__", str(threshold))
            .replace("__VOICE__", voice_str)
            .replace("__LAT__", str(dest_lat))
            .replace("__LON__", str(dest_lon)))

components.html(final_js, height=650)

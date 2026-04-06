import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="ADAS Pro: Auto-Nav", layout="wide")

# --- SIDEBAR: SEARCH ---
st.sidebar.title("🌍 Smart Navigation")
# User types the place name here
destination_query = st.sidebar.text_input("Search Destination", "Petronas Twin Towers")

st.sidebar.divider()
st.sidebar.subheader("🛠️ Vision Calibration")
threshold = st.sidebar.slider("Line Sensitivity", 100, 255, 150)

# JS logic with Nominatim Search Engine integration
JS_CODE = r"""
<div style="position: relative; width: 100%; max-width: 640px; margin: auto; border-radius: 20px; overflow: hidden; background: #000; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
    <video id="video" autoplay playsinline muted style="width: 100%; height: auto; display: block;"></video>
    <canvas id="output" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 5;"></canvas>
    
    <div id="hud" style="position: absolute; top: 15px; left: 15px; color: #00FF00; font-family: monospace; z-index: 10; background: rgba(0,0,0,0.6); padding: 10px; border-radius: 8px;">
        <b>GOAL:</b> <span id="destDisplay">Searching...</span><br>
        <b>DIST:</b> <span id="distDisplay">--</span> km
    </div>

    <div id="overlay" style="position: absolute; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.85); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 100;">
        <h3 style="color: white; font-family: sans-serif;">ADAS PRO: AUTO-ENGINE</h3>
        <button id="startBtn" style="padding: 15px 35px; font-size: 18px; border-radius: 50px; background: #28a745; color: white; border: none; cursor: pointer;">START NAVIGATION</button>
    </div>
</div>

<script>
const video = document.getElementById('video');
const canvas = document.getElementById('output');
const ctx = canvas.getContext('2d', {alpha: true, desynchronized: true});
const destDisplay = document.getElementById('destDisplay');
const distDisplay = document.getElementById('distDisplay');

const THRESHOLD = __THRESHOLD__;
const QUERY = "__QUERY__";

let targetPos = null;
let userPos = null;
let arrowRotation = 0;

// Step 1: Automatically get Lat/Lon from the place name
async function getCoords(query) {
    try {
        const response = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=1`);
        const data = await response.json();
        if (data.length > 0) {
            targetPos = { lat: parseFloat(data[0].lat), lon: parseFloat(data[0].lon) };
            destDisplay.innerText = data[0].display_name.split(',')[0];
            console.log("Target Locked:", targetPos);
        } else {
            destDisplay.innerText = "Location Not Found";
        }
    } catch (e) {
        destDisplay.innerText = "Search Error";
    }
}

// Step 2: Calculate bearing for the AR arrow
function calculateBearing(lat1, lon1, lat2, lon2) {
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const y = Math.sin(dLon) * Math.cos(lat2 * Math.PI / 180);
    const x = Math.cos(lat1 * Math.PI / 180) * Math.sin(lat2 * Math.PI / 180) -
              Math.sin(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.cos(dLon);
    return (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
}

async function start() {
    await getCoords(QUERY); // Auto-fetch coords on start
    
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
    video.srcObject = stream;

    navigator.geolocation.watchPosition(p => {
        userPos = { lat: p.coords.latitude, lon: p.coords.longitude };
        if (targetPos) {
            arrowRotation = calculateBearing(userPos.lat, userPos.lon, targetPos.lat, targetPos.lon);
            // Rough distance calculation
            const d = Math.sqrt(Math.pow(targetPos.lat - userPos.lat, 2) + Math.pow(targetPos.lon - userPos.lon, 2)) * 111;
            distDisplay.innerText = d.toFixed(1);
        }
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
    const w = canvas.width, h = canvas.height;

    // --- LANE DETECTION ---
    const imgData = ctx.getImageData(0, h*0.7, w, h*0.25);
    for (let i = 0; i < imgData.data.length; i += 4) {
        if (imgData.data[i] > THRESHOLD && imgData.data[i+1] > THRESHOLD && imgData.data[i+2] > THRESHOLD) {
            imgData.data[i] = 0; imgData.data[i+1] = 123; imgData.data[i+2] = 255;
        }
    }
    ctx.putImageData(imgData, 0, h*0.7);

    // --- AR ARROW ---
    if (targetPos) {
        ctx.save();
        ctx.translate(w/2, h*0.6);
        ctx.rotate(arrowRotation * Math.PI / 180); 
        ctx.beginPath();
        ctx.moveTo(0, -25); ctx.lineTo(-20, 20); ctx.lineTo(0, 10); ctx.lineTo(20, 20);
        ctx.closePath();
        ctx.fillStyle = "rgba(0, 123, 255, 0.9)"; ctx.strokeStyle = "white"; ctx.lineWidth = 2;
        ctx.stroke(); ctx.fill();
        ctx.restore();
    }

    requestAnimationFrame(render);
}
document.getElementById('startBtn').onclick = start;
</script>
"""

final_js = JS_CODE.replace("__THRESHOLD__", str(threshold)).replace("__QUERY__", destination_query)
components.html(final_js, height=650)

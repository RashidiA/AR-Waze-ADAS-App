import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="ADAS Pro: Open AR", layout="wide")

st.sidebar.title("🌿 Open-Source ADAS")
target_lat = st.sidebar.number_input("Target Lat", value=3.1578, format="%.4f")
target_lon = st.sidebar.number_input("Target Lon", value=101.7123, format="%.4f")

st.sidebar.divider()
st.sidebar.subheader("🛠️ Vision Calibration")
threshold = st.sidebar.slider("Line Sensitivity", 100, 255, 140)

JS_CODE = r"""
<div style="position: relative; width: 100%; max-width: 640px; margin: auto; border-radius: 20px; overflow: hidden; background: #000;">
    <video id="video" autoplay playsinline muted style="width: 100%; height: auto; display: block;"></video>
    <canvas id="output" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 5;"></canvas>
    
    <div id="hud" style="position: absolute; top: 15px; left: 15px; color: #00FF00; font-family: monospace; z-index: 10; background: rgba(0,0,0,0.6); padding: 10px; border-radius: 8px;">
        NAV: OSM ACTIVE<br>
        BRG: <span id="bearing">0</span>°
    </div>

    <div id="overlay" style="position: absolute; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.85); display: flex; align-items: center; justify-content: center; z-index: 100;">
        <button id="startBtn" style="padding: 15px 35px; font-size: 18px; border-radius: 50px; background: #28a745; color: white; border: none; cursor: pointer;">START OPEN ADAS</button>
    </div>
</div>

<script>
const video = document.getElementById('video');
const canvas = document.getElementById('output');
const ctx = canvas.getContext('2d', {alpha: true, desynchronized: true});
const brgDisplay = document.getElementById('bearing');

const THRESHOLD = __THRESHOLD__;
const T_LAT = __T_LAT__;
const T_LON = __T_LON__;

let userPos, arrowRotation = 0;

function calculateBearing(lat1, lon1, lat2, lon2) {
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const y = Math.sin(dLon) * Math.cos(lat2 * Math.PI / 180);
    const x = Math.cos(lat1 * Math.PI / 180) * Math.sin(lat2 * Math.PI / 180) -
              Math.sin(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.cos(dLon);
    return (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
}

async function start() {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
    video.srcObject = stream;

    navigator.geolocation.watchPosition(p => {
        const uLat = p.coords.latitude;
        const uLon = p.coords.longitude;
        arrowRotation = calculateBearing(uLat, uLon, T_LAT, T_LON);
        brgDisplay.innerText = Math.round(arrowRotation);
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

    // --- LANE DETECTION (Adjusted for sensitive detection) ---
    const imgData = ctx.getImageData(0, h*0.7, w, h*0.25);
    for (let i = 0; i < imgData.data.length; i += 4) {
        if (imgData.data[i] > THRESHOLD && imgData.data[i+1] > THRESHOLD && imgData.data[i+2] > THRESHOLD) {
            imgData.data[i] = 0; imgData.data[i+1] = 255; imgData.data[i+2] = 0; // Green for OSM
        }
    }
    ctx.putImageData(imgData, 0, h*0.7);

    // --- AR ARROW ---
    ctx.save();
    ctx.translate(w/2, h*0.6);
    // In a real car, you'd subtract the car's heading from the bearing
    ctx.rotate((arrowRotation) * Math.PI / 180); 
    ctx.beginPath();
    ctx.moveTo(0, -20); ctx.lineTo(-20, 20); ctx.lineTo(0, 10); ctx.lineTo(20, 20);
    ctx.closePath();
    ctx.fillStyle = "#28a745"; ctx.strokeStyle = "white"; ctx.lineWidth = 2;
    ctx.stroke(); ctx.fill();
    ctx.restore();

    requestAnimationFrame(render);
}
document.getElementById('startBtn').onclick = start;
</script>
"""

final_js = (JS_CODE.replace("__THRESHOLD__", str(threshold))
                   .replace("__T_LAT__", str(target_lat))
                   .replace("__T_LON__", str(target_lon)))
components.html(final_js, height=600)

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="ADAS Pro: Google Maps AR", layout="wide")

# --- SIDEBAR: NAVIGATION ---
st.sidebar.title("🗺️ Google Maps AR Engine")
api_key = st.sidebar.text_input("Google Maps API Key", type="password")
destination = st.sidebar.text_input("Enter Destination", "KLCC, Kuala Lumpur")

st.sidebar.divider()
st.sidebar.subheader("🛠️ Vision Tuning")
threshold = st.sidebar.slider("Line Sensitivity", 100, 255, 150)

# RAW STRING used to prevent Python f-string errors with JS braces
JS_TEMPLATE = r"""
<div style="position: relative; width: 100%; max-width: 640px; margin: auto; border-radius: 20px; overflow: hidden; background: #000; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
    <video id="video" autoplay playsinline muted style="width: 100%; height: auto; display: block;"></video>
    <canvas id="output" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 5;"></canvas>
    
    <div id="hud" style="position: absolute; top: 15px; left: 15px; color: #00FF00; font-family: monospace; z-index: 10; background: rgba(0,0,0,0.6); padding: 10px; border-radius: 8px;">
        <b>GOAL:</b> <span id="destName">__DEST__</span><br>
        <b>DIST:</b> <span id="dist">--</span> km
    </div>

    <div id="overlay" style="position: absolute; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.85); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 100;">
        <h3 style="color: white; font-family: sans-serif;">ADAS PRO: GOOGLE AR ENGINE</h3>
        <button id="startBtn" style="padding: 15px 35px; font-size: 18px; border-radius: 50px; background: #4285F4; color: white; border: none; cursor: pointer;">START NAVIGATION</button>
    </div>
</div>

<script src="https://maps.googleapis.com/maps/api/js?key=__API_KEY__&libraries=geometry"></script>

<script>
const video = document.getElementById('video');
const canvas = document.getElementById('output');
const ctx = canvas.getContext('2d', {alpha: true, desynchronized: true});
const distDisplay = document.getElementById('dist');

const THRESHOLD = __THRESHOLD__;
const DESTINATION = "__DEST__";

let userPos, directionsService, arrowRotation = 0;

function drawARArrow(w, h) {
    const x = w / 2;
    const y = h * 0.65;
    const bounce = Math.sin(Date.now() * 0.005) * 15;

    ctx.save();
    ctx.translate(x, y + bounce);
    // Rotate arrow based on Google Maps heading
    ctx.rotate(arrowRotation * Math.PI / 180);
    
    ctx.beginPath();
    ctx.moveTo(0, 0); ctx.lineTo(-25, 35); ctx.lineTo(0, 25); ctx.lineTo(25, 35);
    ctx.closePath();
    ctx.fillStyle = "rgba(66, 133, 244, 0.9)"; // Google Blue
    ctx.strokeStyle = "white";
    ctx.lineWidth = 3;
    ctx.stroke(); ctx.fill();
    ctx.restore();
}

async function start() {
    directionsService = new google.maps.DirectionsService();
    
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
    video.srcObject = stream;

    navigator.geolocation.watchPosition(p => {
        userPos = { lat: p.coords.latitude, lng: p.coords.longitude };
        updateRoute();
    }, null, {enableHighAccuracy: true});

    document.getElementById('overlay').style.display = 'none';
    video.onloadedmetadata = () => {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        render();
    };
}

function updateRoute() {
    if (!userPos || !DESTINATION) return;
    
    directionsService.route({
        origin: userPos,
        destination: DESTINATION,
        travelMode: 'DRIVING'
    }, (result, status) => {
        if (status === 'OK') {
            const route = result.routes[0].legs[0];
            distDisplay.innerText = (route.distance.value / 1000).toFixed(1);
            
            // Get heading of the next step to tilt the arrow
            const nextStep = route.steps[0].start_location;
            const heading = google.maps.geometry.spherical.computeHeading(userPos, nextStep);
            arrowRotation = heading; // This aligns the arrow to the actual road path
        }
    });
}

function render() {
    ctx.drawImage(video, 0, 0);
    const w = canvas.width;
    const h = canvas.height;

    // --- LANE DETECTION ---
    const scanH = Math.floor(h * 0.25);
    const scanTop = Math.floor(h * 0.7);
    const imgData = ctx.getImageData(0, scanTop, w, scanH);
    const pixels = imgData.data;

    for (let i = 0; i < pixels.length; i += 4) {
        if (pixels[i] > THRESHOLD && pixels[i+1] > THRESHOLD && pixels[i+2] > THRESHOLD) {
            pixels[i] = 66; pixels[i+1] = 133; pixels[i+2] = 244; // Google Blue
        }
    }
    ctx.putImageData(imgData, 0, scanTop);

    // --- AR ARROW ---
    drawARArrow(w, h);
    requestAnimationFrame(render);
}

document.getElementById('startBtn').onclick = start;
</script>
"""

# Dynamic Replacement
final_js = (JS_TEMPLATE
            .replace("__API_KEY__", api_key)
            .replace("__DEST__", destination)
            .replace("__THRESHOLD__", str(threshold)))

components.html(final_js, height=650)

import streamlit as st
import streamlit.components.v1 as components
from streamlit_folium import st_folium
import folium
import requests

st.set_page_config(page_title="ADAS Pro: Map Confirm", layout="wide")

# --- SIDEBAR: SEARCH & CONFIRM ---
st.sidebar.title("🌍 Smart Navigation")
query = st.sidebar.text_input("Search Destination", "Petronas Twin Towers")

# Function to get Lat/Lon and address for confirmation
@st.cache_data
def search_location(text):
    if not text: return None
    url = f"https://nominatim.openstreetmap.org/search?q={text}&format=json&limit=1"
    headers = {'User-Agent': 'ADAS-Pro-Research-App'}
    response = requests.get(url, headers=headers).json()
    return response[0] if response else None

location_data = search_location(query)

if location_data:
    lat = float(location_data['lat'])
    lon = float(location_data['lon'])
    address = location_data['display_name'].split(',')[0]
    
    st.sidebar.success(f"📍 Found: {address}")
    
    # --- MINI CONFIRMATION MAP ---
    m = folium.Map(location=[lat, lon], zoom_start=15)
    folium.Marker([lat, lon], popup=address).add_to(m)
    st_folium(m, height=250, width=300, key="preview_map")
else:
    st.sidebar.warning("Waiting for valid destination...")
    lat, lon, address = 0, 0, "None"

st.sidebar.divider()
threshold = st.sidebar.slider("Line Sensitivity", 100, 255, 150)

# --- AR VISION ENGINE ---
JS_CODE = r"""
<div style="position: relative; width: 100%; max-width: 640px; margin: auto; border-radius: 20px; overflow: hidden; background: #000;">
    <video id="video" autoplay playsinline muted style="width: 100%; height: auto; display: block;"></video>
    <canvas id="output" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 5;"></canvas>
    <div id="overlay" style="position: absolute; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.8); display: flex; align-items: center; justify-content: center; z-index: 100;">
        <button id="startBtn" style="padding: 15px 35px; border-radius: 50px; background: #28a745; color: white; border: none; cursor: pointer;">CONFIRM & START AR</button>
    </div>
</div>

<script>
const video = document.getElementById('video');
const canvas = document.getElementById('output');
const ctx = canvas.getContext('2d');

const THRESHOLD = __THRESHOLD__;
const T_LAT = __T_LAT__;
const T_LON = __T_LON__;

let userPos = null;
let arrowRotation = 0;

async function start() {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
    video.srcObject = stream;
    navigator.geolocation.watchPosition(p => {
        userPos = { lat: p.coords.latitude, lon: p.coords.longitude };
        // Math to calculate rotation toward target
        const dLon = (T_LON - userPos.lon) * Math.PI / 180;
        const y = Math.sin(dLon) * Math.cos(T_LAT * Math.PI / 180);
        const x = Math.cos(userPos.lat * Math.PI / 180) * Math.sin(T_LAT * Math.PI / 180) -
                  Math.sin(userPos.lat * Math.PI / 180) * Math.cos(T_LAT * Math.PI / 180) * Math.cos(dLon);
        arrowRotation = (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
    });
    document.getElementById('overlay').style.display = 'none';
    video.onloadedmetadata = () => { canvas.width = video.videoWidth; canvas.height = video.videoHeight; render(); };
}

function render() {
    ctx.drawImage(video, 0, 0);
    const w = canvas.width, h = canvas.height;

    // LANE DETECTION
    const imgData = ctx.getImageData(0, h*0.7, w, h*0.25);
    for (let i = 0; i < imgData.data.length; i += 4) {
        if (imgData.data[i] > THRESHOLD && imgData.data[i+1] > THRESHOLD && imgData.data[i+2] > THRESHOLD) {
            imgData.data[i] = 0; imgData.data[i+1] = 123; imgData.data[i+2] = 255;
        }
    }
    ctx.putImageData(imgData, 0, h*0.7);

    // AR ARROW
    ctx.save();
    ctx.translate(w/2, h*0.6);
    ctx.rotate(arrowRotation * Math.PI / 180);
    ctx.beginPath(); ctx.moveTo(0,-25); ctx.lineTo(-20,20); ctx.lineTo(0,10); ctx.lineTo(20,20); ctx.closePath();
    ctx.fillStyle = "rgba(0, 123, 255, 0.9)"; ctx.fill();
    ctx.restore();

    requestAnimationFrame(render);
}
document.getElementById('startBtn').onclick = start;
</script>
"""

final_js = (JS_CODE.replace("__THRESHOLD__", str(threshold))
                   .replace("__T_LAT__", str(lat))
                   .replace("__T_LON__", str(lon)))
components.html(final_js, height=600)

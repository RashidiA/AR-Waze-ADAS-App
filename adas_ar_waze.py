import streamlit as st
import streamlit.components.v1 as components
from streamlit_folium import st_folium
import folium
import requests

st.set_page_config(page_title="ADAS Pro: HUD Edition", layout="wide")

# --- SIDEBAR: SEARCH & CONFIG ---
st.sidebar.title("🚘 HUD Control Center")
query = st.sidebar.text_input("Set Destination", "Petronas Twin Towers")

@st.cache_data
def search_location(text):
    if not text or len(text) < 3: return None
    url = f"https://nominatim.openstreetmap.org/search?q={text}&format=json&limit=1"
    headers = {'User-Agent': 'ADAS-Pro-HUD-Research'}
    try:
        response = requests.get(url, headers=headers).json()
        return response[0] if response else None
    except: return None

location_data = search_location(query)

if location_data:
    lat, lon = float(location_data['lat']), float(location_data['lon'])
    addr = location_data['display_name'].split(',')[0]
    st.sidebar.success(f"📍 Target: {addr}")
    m = folium.Map(location=[lat, lon], zoom_start=15)
    folium.Marker([lat, lon]).add_to(m)
    st_folium(m, height=200, width=300, key="hud_map")
else:
    lat, lon, addr = 0, 0, "No Destination"

st.sidebar.divider()
threshold = st.sidebar.slider("Lane Sensitivity", 100, 255, 145)
unit = st.sidebar.selectbox("Speed Unit", ["km/h", "mph"])

# --- HYUNDAI STYLE HUD JS ---
JS_CODE = r"""
<div style="position: relative; width: 100%; max-width: 800px; margin: auto; border-radius: 25px; overflow: hidden; background: #000; font-family: 'Segoe UI', Roboto, sans-serif;">
    <video id="video" autoplay playsinline muted style="width: 100%; height: auto; display: block; filter: brightness(0.9);"></video>
    <canvas id="output" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 5;"></canvas>
    
    <div id="hud-container" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 10; color: white;">
        
        <div style="position: absolute; bottom: 40px; left: 40px; text-align: center;">
            <div id="speed" style="font-size: 72px; font-weight: 800; text-shadow: 0 0 20px rgba(0,255,255,0.8); line-height: 1;">0</div>
            <div style="font-size: 18px; letter-spacing: 2px; color: rgba(255,255,255,0.7);">__UNIT__</div>
        </div>

        <div id="lane-msg" style="position: absolute; bottom: 120px; left: 50%; transform: translateX(-50%); font-size: 14px; background: rgba(0,255,255,0.2); padding: 5px 15px; border-radius: 20px; border: 1px solid rgba(0,255,255,0.5); display:none;">
            LANE KEEPING ACTIVE
        </div>

        <div style="position: absolute; bottom: 40px; right: 40px; text-align: right; background: rgba(0,0,0,0.4); padding: 15px; border-radius: 15px; border-right: 4px solid #00dbde;">
            <div style="font-size: 12px; color: #00dbde;">DESTINATION</div>
            <div id="dest-name" style="font-size: 18px; font-weight: bold;">__ADDR__</div>
            <div id="dist-val" style="font-size: 24px; font-weight: bold; margin-top: 5px;">-- <span style="font-size: 14px;">km</span></div>
        </div>
    </div>

    <div id="overlay" style="position: absolute; top:0; left:0; width:100%; height:100%; background: rgba(10,20,30,0.9); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 100;">
        <h2 style="color: #00dbde; letter-spacing: 5px;">ADAS PRO HUD</h2>
        <button id="startBtn" style="margin-top: 20px; padding: 15px 40px; border-radius: 10px; background: linear-gradient(45deg, #00dbde, #fc00ff); color: white; border: none; cursor: pointer; font-weight: bold;">INITIALIZE SYSTEM</button>
    </div>
</div>

<script>
const video = document.getElementById('video');
const canvas = document.getElementById('output');
const ctx = canvas.getContext('2d', {alpha: true, desynchronized: true});
const speedEl = document.getElementById('speed');
const distEl = document.getElementById('dist-val');

const THRESHOLD = __THRESHOLD__;
const T_LAT = __T_LAT__;
const T_LON = __T_LON__;

let userPos = null;
let arrowRot = 0;

async function start() {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment', width: 1280 } });
    video.srcObject = stream;
    
    navigator.geolocation.watchPosition(p => {
        userPos = { lat: p.coords.latitude, lon: p.coords.longitude };
        let s = p.coords.speed || 0;
        speedEl.innerText = "__UNIT__" === "km/h" ? Math.round(s * 3.6) : Math.round(s * 2.237);
        
        if (T_LAT != 0) {
            const dLon = (T_LON - userPos.lon) * Math.PI / 180;
            const y = Math.sin(dLon) * Math.cos(T_LAT * Math.PI / 180);
            const x = Math.cos(userPos.lat * Math.PI / 180) * Math.sin(T_LAT * Math.PI / 180) -
                      Math.sin(userPos.lat * Math.PI / 180) * Math.cos(T_LAT * Math.PI / 180) * Math.cos(dLon);
            arrowRot = (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
            
            const dist = Math.sqrt(Math.pow(T_LAT-userPos.lat, 2) + Math.pow(T_LON-userPos.lon, 2)) * 111;
            distEl.innerHTML = `${dist.toFixed(1)} <span style="font-size: 14px;">km</span>`;
        }
    }, null, {enableHighAccuracy: true});

    document.getElementById('overlay').style.display = 'none';
    video.onloadedmetadata = () => { canvas.width = video.videoWidth; canvas.height = video.videoHeight; render(); };
}

function render() {
    ctx.drawImage(video, 0, 0);
    const w = canvas.width, h = canvas.height;

    // LANE DETECTION (Asari-Rashidi Logic)
    const scanH = Math.floor(h * 0.2);
    const scanTop = Math.floor(h * 0.75);
    const imgData = ctx.getImageData(0, scanTop, w, scanH);
    let detected = false;
    for (let i = 0; i < imgData.data.length; i += 4) {
        if (imgData.data[i] > THRESHOLD && imgData.data[i+1] > THRESHOLD && imgData.data[i+2] > THRESHOLD) {
            imgData.data[i] = 0; imgData.data[i+1] = 219; imgData.data[i+2] = 222; // Cyan HUD Color
            detected = true;
        }
    }
    ctx.putImageData(imgData, 0, scanTop);
    document.getElementById('lane-msg').style.display = detected ? 'block' : 'none';

    // AR NAVIGATION ARROW
    if (T_LAT != 0) {
        ctx.save();
        ctx.translate(w/2, h*0.65);
        ctx.rotate(arrowRot * Math.PI / 180);
        ctx.beginPath();
        ctx.moveTo(0, -30); ctx.lineTo(-25, 25); ctx.lineTo(0, 15); ctx.lineTo(25, 25);
        ctx.closePath();
        ctx.fillStyle = "rgba(0, 219, 222, 0.7)";
        ctx.strokeStyle = "white"; ctx.lineWidth = 3;
        ctx.stroke(); ctx.fill();
        ctx.restore();
    }
    requestAnimationFrame(render);
}
document.getElementById('startBtn').onclick = start;
</script>

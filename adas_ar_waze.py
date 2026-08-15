import streamlit as st
import streamlit.components.v1 as components
from streamlit_folium import st_folium
import folium
import requests

st.set_page_config(page_title="ADAS Pro AR HUD", layout="wide", initial_sidebar_state="expanded")

# --- SIDEBAR CONTROLS ---
st.sidebar.title("🚘 HUD & ADAS Control Center")
query = st.sidebar.text_input("Set Navigation Destination", "Petronas Twin Towers")

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
    st_folium(m, height=180, width=280, key="hud_map")
else:
    lat, lon, addr = 0.0, 0.0, "No Destination"

st.sidebar.divider()
st.sidebar.subheader("🛡️ ADAS Features")
enable_adas = st.sidebar.checkbox("Activate Full ADAS Vision", value=True)
lane_sens = st.sidebar.slider("Lane Sensitivity Threshold", 100, 255, 160)
unit = st.sidebar.selectbox("Speed Unit", ["km/h", "mph"])

# --- FRONTEND (EDGE COMPUTING HUD & ADAS) ---
HUD_CODE = f"""
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs"></script>
  <script src="https://cdn.jsdelivr.net/npm/@tensorflow-models/coco-ssd"></script>
  <style>
    body {{ margin: 0; background: #000; overflow: hidden; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
    .hud-wrapper {{ position: relative; width: 100%; max-width: 960px; height: 540px; margin: auto; border-radius: 16px; overflow: hidden; background: #000; }}
    video {{ display: none; }}
    canvas {{ width: 100%; height: 100%; display: block; }}
    
    /* Overlay HUD Graphics */
    .hud-ui {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 10; }}
    
    /* ADAS Popup Alerts */
    .alert-banner {{
      position: absolute; top: 20px; left: 50%; transform: translateX(-50%);
      padding: 12px 28px; border-radius: 30px; font-weight: bold; font-size: 18px;
      letter-spacing: 1px; display: none; text-shadow: 0 0 10px rgba(0,0,0,0.8);
      animation: pulse 0.8s infinite alternate; z-index: 50;
    }}
    .alert-red {{ background: rgba(255, 0, 55, 0.85); color: #fff; border: 2px solid #ff4d4d; box-shadow: 0 0 20px #ff0037; }}
    .alert-yellow {{ background: rgba(255, 170, 0, 0.85); color: #000; border: 2px solid #ffcc00; box-shadow: 0 0 20px #ffaa00; }}
    .alert-blue {{ background: rgba(0, 219, 222, 0.85); color: #000; border: 2px solid #00ffff; box-shadow: 0 0 20px #00dbde; }}
    
    @keyframes pulse {{
      0% {{ transform: translateX(-50%) scale(1); }}
      100% {{ transform: translateX(-50%) scale(1.05); }}
    }}

    /* Start Button Overlay */
    .starter {{
      position: absolute; top: 0; left: 0; width: 100%; height: 100%;
      background: rgba(5,10,20,0.92); display: flex; flex-direction: column;
      align-items: center; justify-content: center; z-index: 100;
    }}
    .btn-start {{
      padding: 16px 42px; font-size: 18px; font-weight: bold; color: white;
      background: linear-gradient(135deg, #00dbde, #fc00ff); border: none;
      border-radius: 50px; cursor: pointer; box-shadow: 0 0 25px rgba(0,219,222,0.5);
    }}
  </style>
</head>
<body>
  <div class="hud-wrapper">
    <video id="cam" autoplay playsinline muted></video>
    <canvas id="hudCanvas"></canvas>
    
    <div class="hud-ui">
      <div id="adasAlert" class="alert-banner alert-red">⚠️ COLLISION WARNING</div>
    </div>

    <div id="startOverlay" class="starter">
      <h1 style="color: #00dbde; font-size: 28px; letter-spacing: 3px; margin-bottom: 20px;">AR HUD & ADAS VISION</h1>
      <button class="btn-start" onclick="initHUD()">START HUD DISPLAY</button>
    </div>
  </div>

  <script>
    const video = document.getElementById('cam');
    const canvas = document.getElementById('hudCanvas');
    const ctx = canvas.getContext('2d', {{ desynchronized: true }});
    const adasAlert = document.getElementById('adasAlert');
    
    const TARGET_LAT = {lat};
    const TARGET_LON = {lon};
    const ADAS_ACTIVE = {"true" if enable_adas else "false"};
    const LANE_THRESH = {lane_sens};
    const SPEED_UNIT = "{unit}";

    let userPos = null;
    let speed = 0;
    let distKm = 0.0;
    let turnAngle = 0;
    let cocoModel = null;
    let frameCounter = 0;

    // Load AI Model on startup
    if (ADAS_ACTIVE) {{
      cocoSsd.load().then(m => {{ cocoModel = m; console.log("ADAS Engine Ready"); }});
    }}

    async function initHUD() {{
      try {{
        const stream = await navigator.mediaDevices.getUserMedia({{
          video: {{ facingMode: 'environment', width: {{ ideal: 1280 }}, height: {{ ideal: 720 }} }}
        }});
        video.srcObject = stream;
        
        navigator.geolocation.watchPosition(p => {{
          userPos = {{ lat: p.coords.latitude, lon: p.coords.longitude }};
          speed = p.coords.speed ? (SPEED_UNIT === "km/h" ? p.coords.speed * 3.6 : p.coords.speed * 2.237) : 0;
          
          if (TARGET_LAT !== 0) {{
            const dLon = (TARGET_LON - userPos.lon) * Math.PI / 180;
            const y = Math.sin(dLon) * Math.cos(TARGET_LAT * Math.PI / 180);
            const x = Math.cos(userPos.lat * Math.PI / 180) * Math.sin(TARGET_LAT * Math.PI / 180) -
                      Math.sin(userPos.lat * Math.PI / 180) * Math.cos(TARGET_LAT * Math.PI / 180) * Math.cos(dLon);
            turnAngle = (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
            distKm = Math.sqrt(Math.pow(TARGET_LAT-userPos.lat, 2) + Math.pow(TARGET_LON-userPos.lon, 2)) * 111;
          }}
        }}, null, {{ enableHighAccuracy: true }});

        document.getElementById('startOverlay').style.display = 'none';
        video.onloadedmetadata = () => {{
          canvas.width = video.videoWidth || 800;
          canvas.height = video.videoHeight || 450;
          renderHUD();
        }};
      }} catch(err) {{
        alert("Camera permission required for HUD!");
      }}
    }}

    async function renderHUD() {{
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const w = canvas.width;
      const h = canvas.height;

      // --- 1. WHITE LANE DETECTION ---
      let laneDetected = false;
      let scanTop = Math.floor(h * 0.7);
      let scanH = Math.floor(h * 0.25);
      let imgData = ctx.getImageData(0, scanTop, w, scanH);
      let data = imgData.data;

      for (let i = 0; i < data.length; i += 16) {{
        if (data[i] > LANE_THRESH && data[i+1] > LANE_THRESH && data[i+2] > LANE_THRESH) {{
          data[i] = 0; data[i+1] = 219; data[i+2] = 222; // Greenish-Cyan highlight
          laneDetected = true;
        }}
      }}
      ctx.putImageData(imgData, 0, scanTop);

      // --- 2. ADAS AI DETECTION (VEHICLES, TRAFFIC LIGHTS, ROAD SIGNS) ---
      let detectedAlert = "";
      let alertLevel = "";

      if (ADAS_ACTIVE && cocoModel && frameCounter % 4 === 0) {{
        const predictions = await cocoModel.detect(video);
        predictions.forEach(pred => {{
          let [bx, by, bw, bh] = pred.bbox;
          let cls = pred.class;

          // Vehicles & Proximity
          if (['car', 'truck', 'bus', 'motorbike'].includes(cls)) {{
            let isClose = bw > (w * 0.4);
            ctx.strokeStyle = isClose ? '#ff0037' : '#00ffcc';
            ctx.lineWidth = 3;
            ctx.strokeRect(bx, by, bw, bh);

            if (isClose) {{
              detectedAlert = "⚠️ BRAKE! VEHICLE CLOSE";
              alertLevel = "alert-red";
            }}
          }}

          // Traffic Lights
          if (cls === 'traffic light') {{
            ctx.strokeStyle = '#ffcc00';
            ctx.lineWidth = 3;
            ctx.strokeRect(bx, by, bw, bh);
            detectedAlert = "🚦 TRAFFIC LIGHT AHEAD";
            alertLevel = "alert-yellow";
          }}

          // Stop Sign / Road Signs
          if (cls === 'stop sign') {{
            ctx.strokeStyle = '#ff0000';
            ctx.lineWidth = 4;
            ctx.strokeRect(bx, by, bw, bh);
            detectedAlert = "🛑 STOP SIGN DETECTED";
            alertLevel = "alert-red";
          }}
        }});
      }}
      frameCounter++;

      // Trigger Alert Banner
      if (detectedAlert) {{
        adasAlert.innerText = detectedAlert;
        adasAlert.className = `alert-banner ${{alertLevel}}`;
        adasAlert.style.display = 'block';
      }} else if (!laneDetected && ADAS_ACTIVE) {{
        adasAlert.innerText = "⚠️ LANE DEPARTURE WARNING";
        adasAlert.className = 'alert-banner alert-yellow';
        adasAlert.style.display = 'block';
      }} else {{
        adasAlert.style.display = 'none';
      }}

      // --- 3. HUD GRAPHICS OVERLAY (Matched to Reference Sygic UI) ---
      // Speed Indicator
      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 56px sans-serif";
      ctx.fillText(Math.round(speed), w * 0.78, h * 0.35);
      ctx.setFont = "16px sans-serif";
      ctx.fillStyle = "rgba(255,255,255,0.7)";
      ctx.fillText(SPEED_UNIT, w * 0.78 + 75, h * 0.35);

      // AR Curved Turn Guidance Path
      if (TARGET_LAT !== 0) {{
        ctx.save();
        ctx.strokeStyle = "rgba(0, 255, 136, 0.85)";
        ctx.lineWidth = 12;
        ctx.shadowColor = "#00ff88";
        ctx.shadowBlur = 15;
        
        ctx.beginPath();
        ctx.moveTo(w * 0.45, h * 0.85);
        ctx.quadraticCurveTo(w * 0.45, h * 0.55, w * 0.4 + (turnAngle > 180 ? -60 : 60), h * 0.45);
        ctx.stroke();

        // Target distance text
        ctx.fillStyle = "#00ff88";
        ctx.font = "bold 24px sans-serif";
        ctx.fillText(`${{distKm.toFixed(1)}} km`, w * 0.4, h * 0.9);
        ctx.restore();
      }}

      requestAnimationFrame(renderHUD);
    }}
  </script>
</body>
</html>
"""

components.html(HUD_CODE, height=560)

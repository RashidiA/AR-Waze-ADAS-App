import streamlit as st
import streamlit.components.v1 as components
import requests

st.set_page_config(page_title="Split-Screen AR HUD + Google Maps", layout="wide", initial_sidebar_state="expanded")

# --- SIDEBAR CONTROLS ---
st.sidebar.title("🚘 HUD Control Panel")

query = st.sidebar.text_input("Set Navigation Destination", "Petronas Twin Towers, Kuala Lumpur")

@st.cache_data
def search_location(text):
    if not text or len(text) < 3: return None
    url = f"https://nominatim.openstreetmap.org/search?q={text}&format=json&limit=1"
    headers = {'User-Agent': 'ADAS-Pro-HUD'}
    try:
        res = requests.get(url, headers=headers).json()
        if res:
            return {
                "lat": float(res[0]['lat']), 
                "lon": float(res[0]['lon']), 
                "name": res[0]['display_name'].split(',')[0]
            }
    except: return None
    return None

location_data = search_location(query)
if location_data:
    lat, lon, addr = location_data['lat'], location_data['lon'], location_data['name']
    st.sidebar.success(f"📍 Target Loaded: {addr}")
else:
    lat, lon, addr = 3.1579, 101.7116, "Kuala Lumpur" # Default location

st.sidebar.divider()
st.sidebar.subheader("🛡️ ADAS AI Features")
enable_adas = st.sidebar.checkbox("Activate ADAS (Lane & Object Detection)", value=True)
unit = st.sidebar.selectbox("Speed Unit", ["km/h", "mph"])

# --- FRONTEND DUAL HUD (AR CAMERA + GOOGLE MAP QUARTER DISPLAY) ---
HUD_CODE = f"""
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs"></script>
  <script src="https://cdn.jsdelivr.net/npm/@tensorflow-models/coco-ssd"></script>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: #050b14; overflow: hidden; font-family: 'Segoe UI', sans-serif; }}
    
    /* Layout Grid */
    .hud-container {{
      display: grid;
      grid-template-columns: 2.2fr 1fr;
      width: 100%;
      height: 560px;
      max-width: 1100px;
      margin: auto;
      border-radius: 16px;
      overflow: hidden;
      background: #000;
      border: 2px solid rgba(0,219,222,0.3);
    }}

    /* Main Left View: AR Camera */
    .ar-view {{ position: relative; width: 100%; height: 100%; background: #000; }}
    video {{ display: none; }}
    canvas {{ width: 100%; height: 100%; display: block; }}

    /* Right View: Map + Telemetry Panel */
    .side-panel {{
      display: flex;
      flex-direction: column;
      background: #09101d;
      border-left: 2px solid rgba(0,219,222,0.3);
    }}

    /* Top-Right Quarter: Embedded Google Map */
    .map-box {{
      width: 100%;
      height: 60%;
      border-bottom: 2px solid rgba(0,219,222,0.3);
      position: relative;
    }}
    .map-box iframe {{ width: 100%; height: 100%; border: none; }}

    /* Bottom-Right Quarter: Speedometer & Telemetry */
    .telemetry-box {{
      height: 40%;
      padding: 15px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      background: radial-gradient(circle, rgba(0,219,222,0.1) 0%, rgba(9,16,29,1) 90%);
    }}
    .speed-val {{ font-size: 48px; font-weight: bold; color: #fff; text-shadow: 0 0 10px #00dbde; }}
    .speed-unit {{ font-size: 14px; color: #00dbde; text-transform: uppercase; letter-spacing: 2px; }}

    /* Warning Banners */
    .alert-banner {{
      position: absolute; top: 15px; left: 50%; transform: translateX(-50%);
      padding: 10px 20px; border-radius: 20px; font-weight: bold; font-size: 14px;
      display: none; text-shadow: 0 0 10px rgba(0,0,0,0.8); z-index: 50;
      animation: pulse 0.8s infinite alternate;
    }}
    .alert-red {{ background: rgba(255, 0, 55, 0.85); color: #fff; border: 1px solid #ff4d4d; }}
    .alert-yellow {{ background: rgba(255, 170, 0, 0.85); color: #000; border: 1px solid #ffcc00; }}

    @keyframes pulse {{
      0% {{ transform: translateX(-50%) scale(1); }}
      100% {{ transform: translateX(-50%) scale(1.04); }}
    }}

    .starter {{
      position: absolute; top: 0; left: 0; width: 100%; height: 100%;
      background: rgba(5,10,20,0.95); display: flex; flex-direction: column;
      align-items: center; justify-content: center; z-index: 100;
    }}
    .btn-start {{
      padding: 14px 36px; font-size: 16px; font-weight: bold; color: white;
      background: linear-gradient(135deg, #00dbde, #fc00ff); border: none;
      border-radius: 50px; cursor: pointer; box-shadow: 0 0 20px rgba(0,219,222,0.5);
    }}
  </style>
</head>
<body>
  <div class="hud-container">
    
    <!-- LEFT SIDE: REAL-TIME AR HUD & ADAS VISION -->
    <div class="ar-view">
      <video id="cam" autoplay playsinline muted></video>
      <canvas id="hudCanvas"></canvas>
      <div id="adasAlert" class="alert-banner alert-red">⚠️ COLLISION WARNING</div>

      <div id="startOverlay" class="starter">
        <h2 style="color: #00dbde; letter-spacing: 2px; margin-bottom: 20px;">SPLIT-SCREEN AR HUD</h2>
        <button class="btn-start" onclick="initHUD()">START HUD ENGINE</button>
      </div>
    </div>

    <!-- RIGHT SIDE: GOOGLE MAPS + SPEED TELEMETRY -->
    <div class="side-panel">
      <!-- Google Maps Frame -->
      <div class="map-box">
        <iframe 
          src="https://maps.google.com/maps?q={lat},{lon}&z=15&output=embed"
          allowfullscreen>
        </iframe>
      </div>

      <!-- Live Speed & Distance Telemetry -->
      <div class="telemetry-box">
        <div class="speed-val" id="speedDisp">0</div>
        <div class="speed-unit">{unit}</div>
        <div style="color: #aaa; font-size: 12px; margin-top: 8px;" id="distDisp">Target: {addr}</div>
      </div>
    </div>

  </div>

  <script>
    const video = document.getElementById('cam');
    const canvas = document.getElementById('hudCanvas');
    const ctx = canvas.getContext('2d', {{ desynchronized: true }});
    const adasAlert = document.getElementById('adasAlert');
    const speedDisp = document.getElementById('speedDisp');
    
    const TARGET_LAT = {lat};
    const TARGET_LON = {lon};
    const ADAS_ACTIVE = {"true" if enable_adas else "false"};
    const SPEED_UNIT = "{unit}";

    let userPos = null;
    let speed = 0;
    let cocoModel = null;
    let frameCounter = 0;

    if (ADAS_ACTIVE) {{
      cocoSsd.load().then(m => {{ cocoModel = m; }});
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
          speedDisp.innerText = Math.round(speed);
        }}, null, {{ enableHighAccuracy: true }});

        document.getElementById('startOverlay').style.display = 'none';
        video.onloadedmetadata = () => {{
          canvas.width = video.videoWidth || 800;
          canvas.height = video.videoHeight || 450;
          renderHUD();
        }};
      }} catch(err) {{
        alert("Camera and location access required!");
      }}
    }}

    async function renderHUD() {{
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const w = canvas.width;
      const h = canvas.height;

      // --- 1. ADAS AI DETECTION OVER AR CAMERA ---
      let detectedAlert = "";
      let alertLevel = "";

      if (ADAS_ACTIVE && cocoModel && frameCounter % 4 === 0) {{
        const predictions = await cocoModel.detect(video);
        predictions.forEach(pred => {{
          let [bx, by, bw, bh] = pred.bbox;
          let cls = pred.class;

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

          if (cls === 'traffic light') {{
            ctx.strokeStyle = '#ffcc00'; ctx.lineWidth = 3;
            ctx.strokeRect(bx, by, bw, bh);
            detectedAlert = "🚦 TRAFFIC LIGHT"; alertLevel = "alert-yellow";
          }}
        }});
      }}
      frameCounter++;

      if (detectedAlert) {{
        adasAlert.innerText = detectedAlert;
        adasAlert.className = `alert-banner ${{alertLevel}}`;
        adasAlert.style.display = 'block';
      }} else {{
        adasAlert.style.display = 'none';
      }}

      // --- 2. 3D AR OVERLAY ON CAMERA VIEW ---
      ctx.save();
      ctx.strokeStyle = "rgba(0, 255, 136, 0.85)";
      ctx.lineWidth = 10;
      ctx.shadowColor = "#00ff88";
      ctx.shadowBlur = 12;
      
      // Curved AR Navigation Lane
      ctx.beginPath();
      ctx.moveTo(w * 0.5, h * 0.9);
      ctx.quadraticCurveTo(w * 0.5, h * 0.6, w * 0.55, h * 0.45);
      ctx.stroke();
      ctx.restore();

      requestAnimationFrame(renderHUD);
    }}
  </script>
</body>
</html>
"""

components.html(HUD_CODE, height=580)

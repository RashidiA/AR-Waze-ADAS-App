import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AR HUD + Google Navigation", layout="wide", initial_sidebar_state="collapsed")

# --- SIDEBAR (Settings Panel) ---
st.sidebar.title("⚙️ HUD Settings")
enable_adas = st.sidebar.checkbox("Activate ADAS (Lane & Object Detection)", value=True)
unit = st.sidebar.selectbox("Speed Unit", ["km/h", "mph"])

# --- FRONTEND DUAL HUD (HIGH-VISIBILITY IN-HUD SEARCH + AR CAMERA + GOOGLE MAP) ---
HUD_CODE = f"""
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs"></script>
  <script src="https://cdn.jsdelivr.net/npm/@tensorflow-models/coco-ssd"></script>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: #050b14; overflow: hidden; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
    
    /* Layout Container */
    .hud-wrapper {{
      position: relative;
      width: 100%;
      max-width: 1150px;
      height: 580px;
      margin: auto;
      border-radius: 16px;
      overflow: hidden;
      background: #000;
      border: 2px solid rgba(0,219,222,0.4);
      box-shadow: 0 0 25px rgba(0, 219, 222, 0.2);
    }}

    /* HIGH-VISIBILITY FLOATING SEARCH BAR OVER HUD */
    .hud-search-box {{
      position: absolute;
      top: 15px;
      left: 15px;
      z-index: 80;
      display: flex;
      align-items: center;
      gap: 10px;
      background: rgba(9, 16, 29, 0.9);
      padding: 8px 16px;
      border-radius: 30px;
      border: 2px solid #00dbde;
      box-shadow: 0 0 20px rgba(0, 219, 222, 0.6);
      backdrop-filter: blur(10px);
    }}
    .hud-search-input {{
      background: transparent;
      border: none;
      outline: none;
      color: #ffffff;
      font-size: 15px;
      width: 260px;
      font-weight: 600;
    }}
    .hud-search-input::placeholder {{
      color: rgba(255, 255, 255, 0.6);
    }}
    .hud-search-btn {{
      background: linear-gradient(135deg, #00dbde, #fc00ff);
      border: none;
      color: #fff;
      font-weight: bold;
      border-radius: 20px;
      padding: 8px 18px;
      cursor: pointer;
      font-size: 12px;
      letter-spacing: 1px;
      box-shadow: 0 0 10px rgba(252, 0, 255, 0.5);
      transition: transform 0.2s ease;
    }}
    .hud-search-btn:hover {{
      transform: scale(1.05);
    }}

    /* Layout Grid */
    .hud-container {{
      display: grid;
      grid-template-columns: 2.2fr 1.1fr;
      width: 100%;
      height: 100%;
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

    /* Google Map Box */
    .map-box {{
      width: 100%;
      height: 65%;
      border-bottom: 2px solid rgba(0,219,222,0.3);
      position: relative;
    }}
    .map-box iframe {{ width: 100%; height: 100%; border: none; }}

    /* Telemetry Box */
    .telemetry-box {{
      height: 35%;
      padding: 10px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      background: radial-gradient(circle, rgba(0,219,222,0.1) 0%, rgba(9,16,29,1) 90%);
    }}
    .speed-val {{ font-size: 44px; font-weight: bold; color: #fff; text-shadow: 0 0 12px #00dbde; }}
    .speed-unit {{ font-size: 13px; color: #00dbde; text-transform: uppercase; letter-spacing: 2px; }}

    /* Collision & ADAS Alerts */
    .alert-banner {{
      position: absolute; top: 75px; left: 50%; transform: translateX(-50%);
      padding: 10px 22px; border-radius: 20px; font-weight: bold; font-size: 14px;
      display: none; text-shadow: 0 0 10px rgba(0,0,0,0.8); z-index: 50;
      animation: pulse 0.8s infinite alternate;
    }}
    .alert-red {{ background: rgba(255, 0, 55, 0.85); color: #fff; border: 1px solid #ff4d4d; box-shadow: 0 0 15px #ff0037; }}

    @keyframes pulse {{
      0% {{ transform: translateX(-50%) scale(1); }}
      100% {{ transform: translateX(-50%) scale(1.05); }}
    }}

    .starter {{
      position: absolute; top: 0; left: 0; width: 100%; height: 100%;
      background: rgba(5,10,20,0.95); display: flex; flex-direction: column;
      align-items: center; justify-content: center; z-index: 100;
    }}
    .btn-start {{
      padding: 14px 38px; font-size: 16px; font-weight: bold; color: white;
      background: linear-gradient(135deg, #00dbde, #fc00ff); border: none;
      border-radius: 50px; cursor: pointer; box-shadow: 0 0 25px rgba(0,219,222,0.5);
    }}
  </style>
</head>
<body>
  <div class="hud-wrapper">
    
    <!-- HIGH-VISIBILITY FLOATING SEARCH BAR -->
    <div class="hud-search-box">
      <span style="font-size: 16px;">🔍</span>
      <input type="text" id="destinationInput" class="hud-search-input" placeholder="Type destination (e.g. KLCC)..." value="Masjid At-Taqwa TTDI">
      <button class="hud-search-btn" onclick="updateDestination()">NAVIGATE</button>
    </div>

    <div class="hud-container">
      <!-- LEFT: CAMERA + ADAS AR OVERLAY -->
      <div class="ar-view">
        <video id="cam" autoplay playsinline muted></video>
        <canvas id="hudCanvas"></canvas>
        <div id="adasAlert" class="alert-banner alert-red">⚠️ COLLISION WARNING</div>

        <div id="startOverlay" class="starter">
          <h2 style="color: #00dbde; letter-spacing: 2px; margin-bottom: 20px;">AR HUD & ADAS VISION</h2>
          <button class="btn-start" onclick="initHUD()">START AR ENGINE</button>
        </div>
      </div>

      <!-- RIGHT: GOOGLE MAPS + SPEED DISPLAY -->
      <div class="side-panel">
        <div class="map-box">
          <iframe id="gmapFrame" src="https://maps.google.com/maps?q=Masjid%20At-Taqwa%20TTDI&t=&z=15&ie=UTF8&iwloc=&output=embed" allowfullscreen></iframe>
        </div>

        <div class="telemetry-box">
          <div class="speed-val" id="speedDisp">0</div>
          <div class="speed-unit">{unit}</div>
          <div style="color: #00ffcc; font-size: 11px; margin-top: 6px; text-align: center; max-width: 90%; font-weight: bold;" id="targetLabel">
            🎯 Masjid At-Taqwa TTDI
          </div>
        </div>
      </div>
    </div>

  </div>

  <script>
    const video = document.getElementById('cam');
    const canvas = document.getElementById('hudCanvas');
    const ctx = canvas.getContext('2d', {{ desynchronized: true }});
    const adasAlert = document.getElementById('adasAlert');
    const speedDisp = document.getElementById('speedDisp');
    const gmapFrame = document.getElementById('gmapFrame');
    const targetLabel = document.getElementById('targetLabel');
    const destInput = document.getElementById('destinationInput');
    
    const ADAS_ACTIVE = {"true" if enable_adas else "false"};
    const SPEED_UNIT = "{unit}";

    let speed = 0;
    let cocoModel = null;
    let frameCounter = 0;

    // DIRECT HUD GOOGLE MAP SEARCH UPDATE
    function updateDestination() {{
      const query = destInput.value.trim();
      if (!query) return;
      
      const encoded = encodeURIComponent(query);
      gmapFrame.src = `https://maps.google.com/maps?q=${{encoded}}&t=&z=15&ie=UTF8&iwloc=&output=embed`;
      targetLabel.innerText = `🎯 ${{query}}`;
    }}

    // Trigger search when pressing Enter
    destInput.addEventListener("keyup", function(event) {{
      if (event.key === "Enter") updateDestination();
    }});

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

      // ADAS Object Detection Engine
      let detectedAlert = "";
      if (ADAS_ACTIVE && cocoModel && frameCounter % 4 === 0) {{
        const predictions = await cocoModel.detect(video);
        predictions.forEach(pred => {{
          let [bx, by, bw, bh] = pred.bbox;
          if (['car', 'truck', 'bus', 'motorbike'].includes(pred.class)) {{
            let isClose = bw > (w * 0.4);
            ctx.strokeStyle = isClose ? '#ff0037' : '#00ffcc';
            ctx.lineWidth = 3;
            ctx.strokeRect(bx, by, bw, bh);
            if (isClose) detectedAlert = "⚠️ BRAKE! VEHICLE CLOSE";
          }}
        }});
      }}
      frameCounter++;

      if (detectedAlert) {{
        adasAlert.innerText = detectedAlert;
        adasAlert.style.display = 'block';
      }} else {{
        adasAlert.style.display = 'none';
      }}

      // Curved 3D AR Lane Overlay
      ctx.save();
      ctx.strokeStyle = "rgba(0, 255, 136, 0.85)";
      ctx.lineWidth = 10;
      ctx.shadowColor = "#00ff88";
      ctx.shadowBlur = 12;
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

components.html(HUD_CODE, height=600)

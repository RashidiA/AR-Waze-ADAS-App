import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AR HUD + Google Navigation", layout="wide", initial_sidebar_state="collapsed")

# --- SIDEBAR CONTROLS ---
st.sidebar.title("⚙️ HUD Settings")
enable_adas = st.sidebar.checkbox("Activate ADAS (Lane & Object Detection)", value=True)
unit = st.sidebar.selectbox("Speed Unit", ["km/h", "mph"])

# --- MOBILE-READY DUAL HUD ENGINE ---
HUD_CODE = f"""
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs"></script>
  <script src="https://cdn.jsdelivr.net/npm/@tensorflow-models/coco-ssd"></script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #050b14; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; overflow-x: hidden; }}
    
    /* Responsive Wrapper */
    .hud-wrapper {{
      position: relative;
      width: 100%;
      height: 92vh;
      max-height: 650px;
      margin: auto;
      border-radius: 12px;
      overflow: hidden;
      background: #000;
      border: 2px solid rgba(0,219,222,0.4);
    }}

    /* Mobile-Optimized Search Bar */
    .hud-search-box {{
      position: absolute;
      top: 10px;
      left: 10px;
      right: 10px;
      z-index: 80;
      display: flex;
      align-items: center;
      gap: 8px;
      background: rgba(9, 16, 29, 0.92);
      padding: 6px 12px;
      border-radius: 25px;
      border: 1.5px solid #00dbde;
      box-shadow: 0 0 15px rgba(0, 219, 222, 0.5);
      backdrop-filter: blur(8px);
    }}
    .hud-search-input {{
      background: transparent;
      border: none;
      outline: none;
      color: #ffffff;
      font-size: 14px;
      width: 100%;
      font-weight: 500;
    }}
    .hud-search-btn {{
      background: linear-gradient(135deg, #00dbde, #fc00ff);
      border: none;
      color: #fff;
      font-weight: bold;
      border-radius: 18px;
      padding: 6px 14px;
      cursor: pointer;
      font-size: 11px;
      white-space: nowrap;
    }}

    /* Dual Display Layout (Responsive Columns) */
    .hud-container {{
      display: flex;
      flex-direction: row;
      width: 100%;
      height: 100%;
    }}

    @media (max-width: 600px) {{
      .hud-container {{ flex-direction: column; }}
      .ar-view {{ height: 55% !important; }}
      .side-panel {{ height: 45% !important; border-left: none !important; border-top: 2px solid rgba(0,219,222,0.3); }}
    }}

    /* Left AR Camera View */
    .ar-view {{ position: relative; width: 65%; height: 100%; background: #000; flex-grow: 1; }}
    video {{ display: none; }}
    canvas {{ width: 100%; height: 100%; display: block; object-fit: cover; }}

    /* Right Telemetry & Map Panel */
    .side-panel {{
      width: 35%;
      min-width: 140px;
      height: 100%;
      display: flex;
      flex-direction: column;
      background: #09101d;
      border-left: 2px solid rgba(0,219,222,0.3);
    }}

    .map-box {{ width: 100%; height: 60%; border-bottom: 2px solid rgba(0,219,222,0.3); position: relative; }}
    .map-box iframe {{ width: 100%; height: 100%; border: none; }}

    .telemetry-box {{
      height: 40%;
      padding: 8px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      background: radial-gradient(circle, rgba(0,219,222,0.1) 0%, rgba(9,16,29,1) 90%);
    }}
    .speed-val {{ font-size: 36px; font-weight: bold; color: #fff; text-shadow: 0 0 10px #00dbde; }}
    .speed-unit {{ font-size: 11px; color: #00dbde; text-transform: uppercase; letter-spacing: 2px; }}

    /* Warnings */
    .alert-banner {{
      position: absolute; top: 60px; left: 50%; transform: translateX(-50%);
      padding: 6px 16px; border-radius: 15px; font-weight: bold; font-size: 12px;
      display: none; text-shadow: 0 0 8px rgba(0,0,0,0.8); z-index: 50;
      white-space: nowrap;
    }}
    .alert-red {{ background: rgba(255, 0, 55, 0.9); color: #fff; border: 1px solid #ff4d4d; }}

    /* Tap-to-Start Screen for Mobile Permissions */
    .starter {{
      position: absolute; top: 0; left: 0; width: 100%; height: 100%;
      background: rgba(5,10,20,0.96); display: flex; flex-direction: column;
      align-items: center; justify-content: center; z-index: 100; text-align: center; padding: 20px;
    }}
    .btn-start {{
      padding: 12px 30px; font-size: 15px; font-weight: bold; color: white;
      background: linear-gradient(135deg, #00dbde, #fc00ff); border: none;
      border-radius: 50px; cursor: pointer; box-shadow: 0 0 20px rgba(0,219,222,0.6);
    }}
  </style>
</head>
<body>
  <div class="hud-wrapper">
    
    <div class="hud-search-box">
      <span>🔍</span>
      <input type="text" id="destinationInput" class="hud-search-input" placeholder="Search destination..." value="Masjid At-Taqwa TTDI">
      <button class="hud-search-btn" onclick="updateDestination()">GO</button>
    </div>

    <div class="hud-container">
      <div class="ar-view">
        <video id="cam" autoplay playsinline webkit-playsinline muted></video>
        <canvas id="hudCanvas"></canvas>
        <div id="adasAlert" class="alert-banner alert-red">⚠️ BRAKE! VEHICLE CLOSE</div>

        <div id="startOverlay" class="starter">
          <h3 style="color: #00dbde; margin-bottom: 15px;">AR HUD VISION ENGINE</h3>
          <button class="btn-start" onclick="initHUD()">TAP TO START CAMERA</button>
        </div>
      </div>

      <div class="side-panel">
        <div class="map-box">
          <iframe id="gmapFrame" src="https://maps.google.com/maps?q=Masjid%20At-Taqwa%20TTDI&t=&z=15&ie=UTF8&iwloc=&output=embed" allowfullscreen></iframe>
        </div>

        <div class="telemetry-box">
          <div class="speed-val" id="speedDisp">0</div>
          <div class="speed-unit">{unit}</div>
          <div style="color: #00ffcc; font-size: 10px; margin-top: 4px; text-align: center; width: 100%; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;" id="targetLabel">
            🎯 Masjid At-Taqwa TTDI
          </div>
        </div>
      </div>
    </div>

  </div>

  <script>
    const video = document.getElementById('cam');
    const canvas = document.getElementById('hudCanvas');
    const ctx = canvas.getContext('2d');
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

    function updateDestination() {{
      const query = destInput.value.trim();
      if (!query) return;
      const encoded = encodeURIComponent(query);
      gmapFrame.src = `https://maps.google.com/maps?q=${{encoded}}&t=&z=15&ie=UTF8&iwloc=&output=embed`;
      targetLabel.innerText = `🎯 ${{query}}`;
    }}

    destInput.addEventListener("keyup", function(event) {{
      if (event.key === "Enter") updateDestination();
    }});

    if (ADAS_ACTIVE) {{
      cocoSsd.load().then(m => {{ cocoModel = m; }});
    }}

    async function initHUD() {{
      try {{
        const constraints = {{
          video: {{ facingMode: {{ ideal: "environment" }}, width: {{ ideal: 640 }}, height: {{ ideal: 480 }} }}
        }};
        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        video.srcObject = stream;
        await video.play();

        if (navigator.geolocation) {{
          navigator.geolocation.watchPosition(p => {{
            speed = p.coords.speed ? (SPEED_UNIT === "km/h" ? p.coords.speed * 3.6 : p.coords.speed * 2.237) : 0;
            speedDisp.innerText = Math.round(speed);
          }}, null, {{ enableHighAccuracy: true }});
        }}

        document.getElementById('startOverlay').style.display = 'none';
        
        // Dynamically resize canvas to fit mobile screen container
        const resizeCanvas = () => {{
          canvas.width = canvas.clientWidth || 300;
          canvas.height = canvas.clientHeight || 300;
        }};
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);
        
        renderHUD();
      }} catch(err) {{
        alert("Camera Permission Required! Ensure your URL starts with https://");
      }}
    }}

    async function renderHUD() {{
      if (video.readyState === video.HAVE_ENOUGH_DATA) {{
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        const w = canvas.width;
        const h = canvas.height;

        // ADAS Vision Detection
        let detectedAlert = false;
        if (ADAS_ACTIVE && cocoModel && frameCounter % 5 === 0) {{
          const predictions = await cocoModel.detect(video);
          predictions.forEach(pred => {{
            let [bx, by, bw, bh] = pred.bbox;
            let scaleX = w / video.videoWidth;
            let scaleY = h / video.videoHeight;
            let rx = bx * scaleX, ry = by * scaleY, rw = bw * scaleX, rh = bh * scaleY;

            if (['car', 'truck', 'bus', 'motorbike'].includes(pred.class)) {{
              let isClose = rw > (w * 0.45);
              ctx.strokeStyle = isClose ? '#ff0037' : '#00ffcc';
              ctx.lineWidth = 3;
              ctx.strokeRect(rx, ry, rw, rh);
              if (isClose) detectedAlert = true;
            }}
          }});
        }}
        frameCounter++;

        adasAlert.style.display = detectedAlert ? 'block' : 'none';

        // 3D Curved AR Guidance Line
        ctx.save();
        ctx.strokeStyle = "rgba(0, 255, 136, 0.85)";
        ctx.lineWidth = 6;
        ctx.shadowColor = "#00ff88";
        ctx.shadowBlur = 8;
        ctx.beginPath();
        ctx.moveTo(w * 0.5, h * 0.95);
        ctx.quadraticCurveTo(w * 0.5, h * 0.65, w * 0.55, h * 0.45);
        ctx.stroke();
        ctx.restore();
      }}

      requestAnimationFrame(renderHUD);
    }}
  </script>
</body>
</html>
"""

components.html(HUD_CODE, height=620)

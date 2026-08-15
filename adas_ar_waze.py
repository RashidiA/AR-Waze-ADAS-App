import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AR HUD + Voice Navigation", layout="wide", initial_sidebar_state="collapsed")

# --- SIDEBAR CONTROLS ---
st.sidebar.title("⚙️ HUD Settings")
enable_adas = st.sidebar.checkbox("Activate ADAS (Lane & Object Detection)", value=True)
unit = st.sidebar.selectbox("Speed Unit", ["km/h", "mph"])

# --- FRONTEND DUAL HUD (VOICE + COMPACT UI + DIRECT GOOGLE NAV LAUNCHER) ---
HUD_CODE = f"""
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs"></script>
  <script src="https://cdn.jsdelivr.net/npm/@tensorflow-models/coco-ssd"></script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #050b14; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; overflow: hidden; }}
    
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

    /* COMPACT TOP-LEFT CONTROL CLUSTER */
    .hud-controls-container {{
      position: absolute;
      top: 12px;
      left: 12px;
      z-index: 80;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}

    .hud-search-box {{
      display: flex;
      align-items: center;
      gap: 6px;
      background: rgba(9, 16, 29, 0.9);
      padding: 4px 8px 4px 12px;
      border-radius: 25px;
      border: 1.5px solid #00dbde;
      box-shadow: 0 0 15px rgba(0, 219, 222, 0.4);
      backdrop-filter: blur(8px);
      width: 320px;
    }}
    .hud-search-input {{
      background: transparent;
      border: none;
      outline: none;
      color: #ffffff;
      font-size: 13px;
      width: 100%;
      font-weight: 500;
    }}
    .btn-icon {{
      background: rgba(0,219,222,0.2);
      border: 1px solid #00dbde;
      color: #fff;
      border-radius: 50%;
      width: 30px;
      height: 30px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 13px;
      flex-shrink: 0;
    }}
    .btn-start-nav {{
      background: linear-gradient(135deg, #00ff88, #00dbde);
      border: none;
      color: #000;
      font-weight: bold;
      border-radius: 20px;
      padding: 6px 12px;
      cursor: pointer;
      font-size: 11px;
      white-space: nowrap;
      box-shadow: 0 0 10px rgba(0, 255, 136, 0.6);
    }}

    .preset-bar {{ display: flex; gap: 6px; }}
    .chip {{
      background: rgba(9, 16, 29, 0.85);
      border: 1px solid rgba(0,219,222,0.5);
      color: #00ffcc;
      padding: 4px 10px;
      border-radius: 15px;
      font-size: 11px;
      cursor: pointer;
      font-weight: bold;
    }}

    .hud-container {{ display: flex; flex-direction: row; width: 100%; height: 100%; }}
    .ar-view {{ position: relative; width: 65%; height: 100%; background: #000; flex-grow: 1; }}
    video {{ display: none; }}
    canvas {{ width: 100%; height: 100%; display: block; object-fit: cover; }}

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

    .alert-banner {{
      position: absolute; top: 90px; left: 50%; transform: translateX(-50%);
      padding: 6px 16px; border-radius: 15px; font-weight: bold; font-size: 12px;
      display: none; text-shadow: 0 0 8px rgba(0,0,0,0.8); z-index: 50;
    }}
    .alert-red {{ background: rgba(255, 0, 55, 0.9); color: #fff; border: 1px solid #ff4d4d; }}

    .starter {{
      position: absolute; top: 0; left: 0; width: 100%; height: 100%;
      background: rgba(5,10,20,0.96); display: flex; flex-direction: column;
      align-items: center; justify-content: center; z-index: 100; text-align: center;
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
    
    <div class="hud-controls-container">
      <div class="hud-search-box">
        <input type="text" id="destinationInput" class="hud-search-input" placeholder="Type location..." value="Taman Sekiah Makmur">
        <button class="btn-icon" id="micBtn" onclick="startVoiceInput()" title="Voice Search">🎙️</button>
        <button class="btn-start-nav" onclick="launchLiveNavigation()" title="Start Turn-By-Turn Navigation">🚀 START</button>
      </div>

      <div class="preset-bar">
        <div class="chip" onclick="quickNav('Taman Sekiah Makmur')">🏠 Home</div>
        <div class="chip" onclick="quickNav('Petronas')">⛽ Gas</div>
        <div class="chip" onclick="quickNav('KLCC')">📍 KLCC</div>
      </div>
    </div>

    <div class="hud-container">
      <div class="ar-view">
        <video id="cam" autoplay playsinline webkit-playsinline muted></video>
        <canvas id="hudCanvas"></canvas>
        <div id="adasAlert" class="alert-banner alert-red">⚠️ BRAKE! VEHICLE CLOSE</div>

        <div id="startOverlay" class="starter">
          <h3 style="color: #00dbde; margin-bottom: 15px;">AR HUD VISION ENGINE</h3>
          <button class="btn-start" onclick="initHUD()">START CAMERA ENGINE</button>
        </div>
      </div>

      <div class="side-panel">
        <div class="map-box">
          <iframe id="gmapFrame" src="https://maps.google.com/maps?q=Taman%20Sekiah%20Makmur&t=&z=15&ie=UTF8&iwloc=&output=embed" allowfullscreen></iframe>
        </div>

        <div class="telemetry-box">
          <div class="speed-val" id="speedDisp">0</div>
          <div class="speed-unit">{unit}</div>
          <div style="color: #00ffcc; font-size: 10px; margin-top: 4px; text-align: center; width: 90%; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;" id="targetLabel">
            🎯 Taman Sekiah Makmur
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
    const micBtn = document.getElementById('micBtn');
    
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

    // LAUNCH NATIVE FULL TURN-BY-TURN NAVIGATION
    function launchLiveNavigation() {{
      const query = destInput.value.trim();
      if (!query) return;
      const encoded = encodeURIComponent(query);
      // Trigger Google Navigation mode directly using google.navigation API scheme
      const navUrl = `https://www.google.com/maps/dir/?api=1&destination=${{encoded}}&travelmode=driving`;
      window.open(navUrl, '_blank');
    }}

    function quickNav(place) {{
      destInput.value = place;
      updateDestination();
    }}

    function startVoiceInput() {{
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognition) {{
        alert("Voice recognition is not supported on this browser.");
        return;
      }}
      const recognition = new SpeechRecognition();
      recognition.lang = 'en-US';
      micBtn.style.background = '#ff0055';

      recognition.onresult = function(event) {{
        const spokenText = event.results[0][0].transcript;
        destInput.value = spokenText;
        micBtn.style.background = 'rgba(0,219,222,0.2)';
        updateDestination();
      }};
      recognition.onerror = function() {{ micBtn.style.background = 'rgba(0,219,222,0.2)'; }};
      recognition.start();
    }}

    destInput.addEventListener("keyup", function(event) {{
      if (event.key === "Enter") updateDestination();
    }});

    if (ADAS_ACTIVE) {{
      cocoSsd.load().then(m => {{ cocoModel = m; }});
    }}

    async function initHUD() {{
      try {{
        const constraints = {{ video: {{ facingMode: {{ ideal: "environment" }} }} }};
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
        
        const resizeCanvas = () => {{
          canvas.width = canvas.clientWidth || 300;
          canvas.height = canvas.clientHeight || 300;
        }};
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);
        
        renderHUD();
      }} catch(err) {{
        alert("Camera permission required!");
      }}
    }}

    async function renderHUD() {{
      if (video.readyState === video.HAVE_ENOUGH_DATA) {{
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        const w = canvas.width;
        const h = canvas.height;

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

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AR HUD + Navigation", layout="wide", initial_sidebar_state="collapsed")

# --- SIDEBAR CONTROLS ---
st.sidebar.title("⚙️ HUD Settings")
enable_adas = st.sidebar.checkbox("Activate ADAS Object Detection", value=True)
unit = st.sidebar.selectbox("Speed Unit", ["km/h", "mph"])

# --- HIGH-PERFORMANCE AR HUD + DYNAMIC WHITE LANE DETECTOR ---
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

    .hud-controls-container {{
      position: absolute;
      top: 10px;
      left: 10px;
      z-index: 80;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}

    .hud-search-box {{
      display: flex;
      align-items: center;
      gap: 6px;
      background: rgba(9, 16, 29, 0.92);
      padding: 4px 8px 4px 10px;
      border-radius: 25px;
      border: 1.5px solid #00dbde;
      box-shadow: 0 0 12px rgba(0, 219, 222, 0.4);
      backdrop-filter: blur(8px);
      width: 310px;
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
      width: 28px;
      height: 28px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      flex-shrink: 0;
    }}
    .btn-start-nav {{
      background: linear-gradient(135deg, #00d2ff, #0072ff);
      border: none;
      color: #fff;
      font-weight: bold;
      border-radius: 18px;
      padding: 5px 12px;
      cursor: pointer;
      font-size: 11px;
      white-space: nowrap;
    }}

    .preset-bar {{ display: flex; gap: 6px; }}
    .chip {{
      background: rgba(9, 16, 29, 0.85);
      border: 1px solid rgba(0,219,222,0.5);
      color: #00ffcc;
      padding: 3px 8px;
      border-radius: 12px;
      font-size: 10px;
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
      position: absolute; top: 85px; left: 50%; transform: translateX(-50%);
      padding: 5px 14px; border-radius: 12px; font-weight: bold; font-size: 11px;
      display: none; z-index: 50; white-space: nowrap;
    }}
    .alert-red {{ background: rgba(255, 0, 55, 0.9); color: #fff; border: 1px solid #ff4d4d; }}

    .starter {{
      position: absolute; top: 0; left: 0; width: 100%; height: 100%;
      background: rgba(5,10,20,0.96); display: flex; flex-direction: column;
      align-items: center; justify-content: center; z-index: 100; text-align: center;
    }}
    .btn-start {{
      padding: 12px 30px; font-size: 15px; font-weight: bold; color: white;
      background: linear-gradient(135deg, #00d2ff, #0072ff); border: none;
      border-radius: 50px; cursor: pointer; box-shadow: 0 0 20px rgba(0,210,255,0.6);
    }}
  </style>
</head>
<body>
  <div class="hud-wrapper">
    
    <div class="hud-controls-container">
      <div class="hud-search-box">
        <input type="text" id="destinationInput" class="hud-search-input" placeholder="Type location..." value="Taman Sekiah Makmur">
        <button class="btn-icon" id="micBtn" onclick="startVoiceInput()" title="Voice Search">🎙️</button>
        <button class="btn-start-nav" onclick="startInAppRoute()" title="Load Route in App">START</button>
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
          <h3 style="color: #00d2ff; margin-bottom: 15px;">AR HUD VISION ENGINE</h3>
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
    let isDetecting = false;

    function startInAppRoute() {{
      const query = destInput.value.trim();
      if (!query) return;
      const encoded = encodeURIComponent(query);
      gmapFrame.src = `https://maps.google.com/maps?q=directions+to+${{encoded}}&t=&z=14&ie=UTF8&iwloc=&output=embed`;
      targetLabel.innerText = `🎯 ${{query}}`;
    }}

    function quickNav(place) {{
      destInput.value = place;
      startInAppRoute();
    }}

    function startVoiceInput() {{
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognition) return alert("Voice search not supported.");
      const recognition = new SpeechRecognition();
      recognition.lang = 'en-US';
      micBtn.style.background = '#ff0055';

      recognition.onresult = function(event) {{
        destInput.value = event.results[0][0].transcript;
        micBtn.style.background = 'rgba(0,219,222,0.2)';
        startInAppRoute();
      }};
      recognition.onerror = function() {{ micBtn.style.background = 'rgba(0,219,222,0.2)'; }};
      recognition.start();
    }}

    destInput.addEventListener("keyup", function(e) {{
      if (e.key === "Enter") startInAppRoute();
    }});

    if (ADAS_ACTIVE) {{
      cocoSsd.load({{ base: 'lite_mobilenet_v2' }}).then(m => {{ cocoModel = m; }});
    }}

    async function initHUD() {{
      try {{
        const stream = await navigator.mediaDevices.getUserMedia({{
          video: {{ facingMode: {{ ideal: "environment" }}, width: 480, height: 360 }}
        }});
        video.srcObject = stream;
        await video.play();

        if (navigator.geolocation) {{
          navigator.geolocation.watchPosition(p => {{
            speed = p.coords.speed ? (SPEED_UNIT === "km/h" ? p.coords.speed * 3.6 : p.coords.speed * 2.237) : 0;
            speedDisp.innerText = Math.round(speed);
          }}, null, {{ enableHighAccuracy: true }});
        }}

        document.getElementById('startOverlay').style.display = 'none';
        canvas.width = 480;
        canvas.height = 360;
        renderHUD();
      }} catch(err) {{
        alert("Camera permission required!");
      }}
    }}

    // DYNAMIC WHITE LANE DETECTION ALGORITHM (BOTH CONTINUOUS & DASHED)
    function detectWhiteLanesAndDrawBlue(w, h) {{
      const imgData = ctx.getImageData(0, Math.floor(h * 0.55), w, Math.floor(h * 0.45));
      const data = imgData.data;
      
      let leftLanePoints = [];
      let rightLanePoints = [];
      const stepY = 12; // Sample every 12th row
      const halfW = w / 2;

      for (let y = 0; y < imgData.height; y += stepY) {{
        let screenY = Math.floor(h * 0.55) + y;
        
        // Scan Left Side for High Brightness (White Lane Pixels)
        for (let x = 20; x < halfW - 20; x += 4) {{
          let i = (y * w + x) * 4;
          let r = data[i], g = data[i+1], b = data[i+2];
          // Threshold for detecting white road marking pixels
          if (r > 175 && g > 175 && b > 175) {{
            leftLanePoints.push({{ x: x, y: screenY }});
            break;
          }}
        }}

        // Scan Right Side for High Brightness (White Lane Pixels)
        for (let x = w - 20; x > halfW + 20; x -= 4) {{
          let i = (y * w + x) * 4;
          let r = data[i], g = data[i+1], b = data[i+2];
          if (r > 175 && g > 175 && b > 175) {{
            rightLanePoints.push({{ x: x, y: screenY }});
            break;
          }}
        }}
      }}

      ctx.save();
      ctx.strokeStyle = "#00d2ff"; // NEON BLUE
      ctx.lineWidth = 5;
      ctx.shadowColor = "#00d2ff";
      ctx.shadowBlur = 10;

      // Draw Left Lane (Works for both solid & dashed)
      if (leftLanePoints.length > 1) {{
        ctx.beginPath();
        ctx.moveTo(leftLanePoints[0].x, leftLanePoints[0].y);
        for (let p of leftLanePoints) ctx.lineTo(p.x, p.y);
        ctx.stroke();
      }} else {{
        // Fallback default left boundary if road is poorly lit
        ctx.beginPath();
        ctx.moveTo(w * 0.15, h);
        ctx.lineTo(w * 0.42, h * 0.58);
        ctx.stroke();
      }}

      // Draw Right Lane (Works for both solid & dashed)
      if (rightLanePoints.length > 1) {{
        ctx.beginPath();
        ctx.moveTo(rightLanePoints[0].x, rightLanePoints[0].y);
        for (let p of rightLanePoints) ctx.lineTo(p.x, p.y);
        ctx.stroke();
      }} else {{
        // Fallback default right boundary if road is poorly lit
        ctx.beginPath();
        ctx.moveTo(w * 0.85, h);
        ctx.lineTo(w * 0.58, h * 0.58);
        ctx.stroke();
      }}

      ctx.restore();
    }}

    async function renderHUD() {{
      if (video.readyState === video.HAVE_ENOUGH_DATA) {{
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        const w = canvas.width;
        const h = canvas.height;

        // DYNAMIC WHITE LANE DETECTION
        detectWhiteLanesAndDrawBlue(w, h);

        // THROTTLED ADAS DETECTION (Runs smoothly every 10 frames)
        if (ADAS_ACTIVE && cocoModel && !isDetecting && frameCounter % 10 === 0) {{
          isDetecting = true;
          cocoModel.detect(video).then(predictions => {{
            let alertTriggered = false;
            predictions.forEach(pred => {{
              if (['car', 'truck', 'bus', 'motorbike'].includes(pred.class)) {{
                let [bx, by, bw, bh] = pred.bbox;
                if (bw > (w * 0.4)) alertTriggered = true;
              }}
            }});
            adasAlert.style.display = alertTriggered ? 'block' : 'none';
            isDetecting = false;
          }}).catch(() => {{ isDetecting = false; }});
        }}
        frameCounter++;
      }}

      requestAnimationFrame(renderHUD);
    }}
  </script>
</body>
</html>
"""

components.html(HUD_CODE, height=620)

import streamlit as st
import streamlit.components.v1 as components
import requests

st.set_page_config(page_title="ADAS AR HUD - OSRM Engine", layout="wide", initial_sidebar_state="expanded")

# --- SIDEBAR CONTROLS ---
st.sidebar.title("🚘 Open-Source HUD Control Center")
st.sidebar.caption("Powered by **OSRM Routing Engine** & **Hardware Compass Fusion**")

query = st.sidebar.text_input("Set Navigation Destination", "Petronas Twin Towers, Kuala Lumpur")

@st.cache_data
def search_location_free(text):
    if not text or len(text) < 3: return None
    url = f"https://nominatim.openstreetmap.org/search?q={text}&format=json&limit=1"
    headers = {'User-Agent': 'ADAS-Pro-HUD-OpenSource'}
    try:
        res = requests.get(url, headers=headers).json()
        if res:
            return {
                "lat": float(res[0]['lat']), 
                "lon": float(res[0]['lon']), 
                "name": res[0]['display_name'].split(',')[0]
            }
    except Exception as e:
        return None
    return None

location_data = search_location_free(query)

if location_data:
    lat, lon, addr = location_data['lat'], location_data['lon'], location_data['name']
    st.sidebar.success(f"📍 Target: {addr}")
else:
    lat, lon, addr = 0.0, 0.0, "No Destination"

st.sidebar.divider()
st.sidebar.subheader("🛡️ ADAS Vision Settings")
enable_adas = st.sidebar.checkbox("Activate ADAS (Lane & Object Detection)", value=True)
lane_sens = st.sidebar.slider("Lane Sensitivity Threshold", 100, 255, 160)
unit = st.sidebar.selectbox("Speed Unit", ["km/h", "mph"])

# --- FRONTEND (OSRM ROUTING + COMPASS AR FUSION + ADAS) ---
HUD_CODE = f"""
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs"></script>
  <script src="https://cdn.jsdelivr.net/npm/@tensorflow-models/coco-ssd"></script>
  <style>
    body {{ margin: 0; background: #000; overflow: hidden; font-family: 'Segoe UI', sans-serif; }}
    .hud-wrapper {{ position: relative; width: 100%; max-width: 960px; height: 540px; margin: auto; border-radius: 16px; overflow: hidden; background: #000; }}
    video {{ display: none; }}
    canvas {{ width: 100%; height: 100%; display: block; }}
    
    .alert-banner {{
      position: absolute; top: 20px; left: 50%; transform: translateX(-50%);
      padding: 12px 28px; border-radius: 30px; font-weight: bold; font-size: 18px;
      letter-spacing: 1px; display: none; text-shadow: 0 0 10px rgba(0,0,0,0.8);
      animation: pulse 0.8s infinite alternate; z-index: 50;
    }}
    .alert-red {{ background: rgba(255, 0, 55, 0.85); color: #fff; border: 2px solid #ff4d4d; box-shadow: 0 0 20px #ff0037; }}
    .alert-yellow {{ background: rgba(255, 170, 0, 0.85); color: #000; border: 2px solid #ffcc00; box-shadow: 0 0 20px #ffaa00; }}
    
    @keyframes pulse {{
      0% {{ transform: translateX(-50%) scale(1); }}
      100% {{ transform: translateX(-50%) scale(1.05); }}
    }}

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
    
    <div id="adasAlert" class="alert-banner alert-red">⚠️ COLLISION WARNING</div>

    <div id="startOverlay" class="starter">
      <h1 style="color: #00dbde; font-size: 24px; letter-spacing: 2px; margin-bottom: 20px;">AR HUD & ADAS (OSRM ENGINE)</h1>
      <button class="btn-start" onclick="initHUD()">START AR NAVIGATION</button>
    </div>
  </div>

  <script>
    const video = document.getElementById('cam');
    const canvas = document.getElementById('hudCanvas');
    const ctx = canvas.getContext('2d', {{ desynchronized: true }});
    const adasAlert = document.getElementById('adasAlert');
    
    const TARGET_LAT = {lat};
    const TARGET_LON = {lon};
    const DEST_NAME = "{addr}";
    const ADAS_ACTIVE = {"true" if enable_adas else "false"};
    const LANE_THRESH = {lane_sens};
    const SPEED_UNIT = "{unit}";

    let userPos = null;
    let phoneHeading = 0; // Hardware compass orientation
    let speed = 0;
    let distKm = 0.0;
    let targetBearing = 0;
    let nextManeuver = "Straight";
    let cocoModel = null;
    let frameCounter = 0;
    let routeFetched = false;

    // --- 1. HARDWARE COMPASS SENSOR ENGINE ---
    function initCompass() {{
      if (window.DeviceOrientationEvent) {{
        window.addEventListener('deviceorientation', (e) => {{
          if (e.webkitCompassHeading) {{
            phoneHeading = e.webkitCompassHeading; // iOS support
          }} else if (e.alpha !== null) {{
            phoneHeading = 360 - e.alpha; // Android support
          }}
        }}, true);
      }}
    }}

    // --- 2. OSRM ROUTING ENGINE INTEGRATION (100% FREE) ---
    async function fetchOSRMRoute(userLat, userLon, tgtLat, tgtLon) {{
      const url = `https://router.project-osrm.org/route/v1/driving/${{userLon}},${{userLat}};${{tgtLon}},${{tgtLat}}?overview=full&steps=true&geometries=geojson`;
      try {{
        const response = await fetch(url);
        const data = await response.json();
        if (data.routes && data.routes.length > 0) {{
          const route = data.routes[0];
          distKm = route.distance / 1000.0;
          
          if (route.legs[0].steps.length > 0) {{
            const nextStep = route.legs[0].steps[1] || route.legs[0].steps[0];
            const maneuverType = nextStep.maneuver.type;
            const modifier = nextStep.maneuver.modifier || "";
            
            if (modifier.includes("right")) nextManeuver = "Right Turn";
            else if (modifier.includes("left")) nextManeuver = "Left Turn";
            else nextManeuver = "Continue Straight";

            // Next step bearing
            const stepLoc = nextStep.maneuver.location;
            targetBearing = calcBearing(userLat, userLon, stepLoc[1], stepLoc[0]);
          }}
        }}
      }} catch (err) {{
        console.warn("OSRM fallback to direct bearing", err);
        targetBearing = calcBearing(userLat, userLon, tgtLat, tgtLon);
      }}
    }}

    function calcBearing(lat1, lon1, lat2, lon2) {{
      const dLon = (lon2 - lon1) * Math.PI / 180;
      const y = Math.sin(dLon) * Math.cos(lat2 * Math.PI / 180);
      const x = Math.cos(lat1 * Math.PI / 180) * Math.sin(lat2 * Math.PI / 180) -
                Math.sin(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.cos(dLon);
      return (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
    }}

    if (ADAS_ACTIVE) {{
      cocoSsd.load().then(m => {{ cocoModel = m; }});
    }}

    async function initHUD() {{
      initCompass();
      try {{
        const stream = await navigator.mediaDevices.getUserMedia({{
          video: {{ facingMode: 'environment', width: {{ ideal: 1280 }}, height: {{ ideal: 720 }} }}
        }});
        video.srcObject = stream;
        
        navigator.geolocation.watchPosition(p => {{
          userPos = {{ lat: p.coords.latitude, lon: p.coords.longitude }};
          speed = p.coords.speed ? (SPEED_UNIT === "km/h" ? p.coords.speed * 3.6 : p.coords.speed * 2.237) : 0;
          
          if (TARGET_LAT !== 0 && !routeFetched) {{
            fetchOSRMRoute(userPos.lat, userPos.lon, TARGET_LAT, TARGET_LON);
            routeFetched = true;
          }}
        }}, null, {{ enableHighAccuracy: true }});

        document.getElementById('startOverlay').style.display = 'none';
        video.onloadedmetadata = () => {{
          canvas.width = video.videoWidth || 800;
          canvas.height = video.videoHeight || 450;
          renderHUD();
        }};
      }} catch(err) {{
        alert("Camera and location permissions required!");
      }}
    }}

    async function renderHUD() {{
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const w = canvas.width;
      const h = canvas.height;

      // --- 3. WHITE LANE DETECTION ---
      let laneDetected = false;
      let scanTop = Math.floor(h * 0.7);
      let scanH = Math.floor(h * 0.25);
      let imgData = ctx.getImageData(0, scanTop, w, scanH);
      let data = imgData.data;

      for (let i = 0; i < data.length; i += 16) {{
        if (data[i] > LANE_THRESH && data[i+1] > LANE_THRESH && data[i+2] > LANE_THRESH) {{
          data[i] = 0; data[i+1] = 219; data[i+2] = 222;
          laneDetected = true;
        }}
      }}
      ctx.putImageData(imgData, 0, scanTop);

      // --- 4. ADAS AI OBJECT DETECTION ---
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
            detectedAlert = "🚦 TRAFFIC LIGHT AHEAD"; alertLevel = "alert-yellow";
          }}

          if (cls === 'stop sign') {{
            ctx.strokeStyle = '#ff0000'; ctx.lineWidth = 4;
            ctx.strokeRect(bx, by, bw, bh);
            detectedAlert = "🛑 STOP SIGN DETECTED"; alertLevel = "alert-red";
          }}
        }});
      }}
      frameCounter++;

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

      // --- 5. SPATIAL AR NAVIGATION DISPLAY ---
      // Speed Overlay
      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 56px sans-serif";
      ctx.fillText(Math.round(speed), w * 0.78, h * 0.35);
      ctx.font = "16px sans-serif";
      ctx.fillStyle = "rgba(255,255,255,0.7)";
      ctx.fillText(SPEED_UNIT, w * 0.78 + 75, h * 0.35);

      // Destination Info Box
      ctx.fillStyle = "rgba(0,0,0,0.5)";
      ctx.fillRect(w * 0.05, h * 0.75, 260, 80);
      ctx.fillStyle = "#00dbde";
      ctx.font = "bold 14px sans-serif";
      ctx.fillText("DESTINATION (OSRM)", w * 0.07, h * 0.80);
      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 15px sans-serif";
      ctx.fillText(DEST_NAME.length > 20 ? DEST_NAME.substring(0, 20) + "..." : DEST_NAME, w * 0.07, h * 0.86);

      // SPATIAL AR ARROW ANCHORING VIA COMPASS FUSION
      if (TARGET_LAT !== 0) {{
        let diff = targetBearing - phoneHeading;
        if (diff > 180) diff -= 360;
        if (diff < -180) diff += 360;

        // Map angular compass offset onto canvas X axis
        const fov = 60; // Approximate camera field of view
        const arX = (w / 2) + ((diff / (fov / 2)) * (w / 2));
        const clampedX = Math.max(w * 0.2, Math.min(w * 0.8, arX));

        ctx.save();
        ctx.strokeStyle = "rgba(0, 255, 136, 0.9)";
        ctx.lineWidth = 14;
        ctx.shadowColor = "#00ff88";
        ctx.shadowBlur = 18;
        
        // Dynamic Curved Path projecting onto lane
        ctx.beginPath();
        ctx.moveTo(w * 0.5, h * 0.9);
        ctx.quadraticCurveTo(w * 0.5, h * 0.6, clampedX, h * 0.45);
        ctx.stroke();

        ctx.fillStyle = "#00ff88";
        ctx.font = "bold 20px sans-serif";
        ctx.fillText(`${{nextManeuver}} (${{distKm.toFixed(1)}} km)`, w * 0.38, h * 0.93);
        ctx.restore();
      }}

      requestAnimationFrame(renderHUD);
    }}
  </script>
</body>
</html>
"""

components.html(HUD_CODE, height=560)

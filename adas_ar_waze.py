import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="ADAS Pro: AR Waze Edition", layout="wide")

# --- SIDEBAR CONTROLS ---
st.sidebar.title("🎙️ System Controls")
enable_voice = st.sidebar.toggle("Enable Voice Alerts", value=True)
show_weather = st.sidebar.toggle("Show Weather HUD", value=True)
drift_sensitivity = st.sidebar.slider("Lane Drift Sensitivity", 50, 150, 100)

voice_flag = "true" if enable_voice else "false"
weather_flag = "true" if show_weather else "false"

JS_CODE = f"""
<div style="position: relative; width: 100%; max-width: 640px; margin: auto; border-radius: 20px; overflow: hidden; background: #000; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
    <video id="video" autoplay playsinline style="width: 100%; height: auto; display: block;"></video>
    <canvas id="output" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></canvas>
    
    <div id="hud" style="position: absolute; top: 20px; left: 20px; color: white; font-family: monospace; pointer-events: none;">
        <div style="background: rgba(0,123,255,0.7); padding: 8px 15px; border-radius: 5px; margin-bottom: 5px; font-weight: bold;">
            📍 AR WAZE ACTIVE
        </div>
        <div style="background: rgba(0,0,0,0.6); padding: 8px 15px; border-radius: 5px; font-size: 14px;">
            SPD: <span id="speed" style="color: #00FF00; font-weight: bold;">0.0</span> km/h<br>
            <span id="weatherData" style="display: none;">TEMP: <span id="temp">--</span>°C | CLEAR</span>
        </div>
    </div>

    <div id="overlay" style="position: absolute; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.9); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 100;">
        <h2 style="color: white; font-family: sans-serif;">ASARI-RASHIDI PRO</h2>
        <button id="startBtn" style="padding: 18px 40px; font-size: 20px; border-radius: 50px; background: #007bff; color: white; border: none; cursor: pointer;">START SYSTEM</button>
    </div>
</div>

<script>
const video = document.getElementById('video');
const canvas = document.getElementById('output');
const ctx = canvas.getContext('2d', {{alpha: false, desynchronized: true}});
const speedVal = document.getElementById('speed');
const tempVal = document.getElementById('temp');
const weatherDisplay = document.getElementById('weatherData');

let lastSpeechTime = 0;
const synth = window.speechSynthesis;

function speak(text) {{
    if (!{voice_flag}) return;
    const now = Date.now();
    if (now - lastSpeechTime < 5000) return; 
    const utterance = new SpeechSynthesisUtterance(text);
    synth.speak(utterance);
    lastSpeechTime = now;
}}

async function fetchWeather(lat, lon) {{
    try {{
        const res = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${{lat}}&longitude=${{lon}}&current_weather=true`);
        const data = await res.json();
        tempVal.innerText = data.current_weather.temperature;
        if ({weather_flag}) weatherDisplay.style.display = "block";
    }} catch(e) {{ console.log("Weather failed"); }}
}}

async function startSystem() {{
    const stream = await navigator.mediaDevices.getUserMedia({{ 
        video: {{ facingMode: 'environment', width: 640 }} 
    }});
    video.srcObject = stream;
    document.getElementById('overlay').style.display = 'none';
    speak("System initialized.");

    navigator.geolocation.getCurrentPosition(pos => {{
        fetchWeather(pos.coords.latitude, pos.coords.longitude);
    }});

    navigator.geolocation.watchPosition(pos => {{
        speedVal.innerText = ((pos.coords.speed || 0) * 3.6).toFixed(1);
    }}, null, {{enableHighAccuracy: true}});

    video.onloadedmetadata = () => render();
}}

function render() {{
    canvas.width = video.videoWidth; canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);
    const h = canvas.height; const w = canvas.width;
    const roadTop = Math.floor(h * 0.7);
    const roadData = ctx.getImageData(0, roadTop, w, Math.floor(h * 0.3));
    const pixels = roadData.data;
    let leftCount = 0; let rightCount = 0;

    for (let i = 0; i < pixels.length; i += 4) {{
        if (pixels[i] > 205 && pixels[i+1] > 205 && pixels[i+2] > 205) {{
            pixels[i] = 0; pixels[i+1] = 123; pixels[i+2] = 255;
            let xPos = (i / 4) % w;
            if (xPos < w * 0.3) leftCount++;
            if (xPos > w * 0.7) rightCount++;
        }}
    }
    ctx.putImageData(roadData, 0, roadTop);
    if (leftCount > {drift_sensitivity}) speak("Check left lane");
    if (rightCount > {drift_sensitivity}) speak("Check right lane");
    requestAnimationFrame(render);
}}
document.getElementById('startBtn').onclick = startSystem;
</script>
"""
components.html(JS_CODE, height=650)

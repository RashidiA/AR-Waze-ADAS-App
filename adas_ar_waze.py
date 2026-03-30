import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="ADAS Pro: Mobile Edge AI", layout="wide")

# --- SIDEBAR CONTROLS ---
st.sidebar.title("🎙️ ADAS Pro Settings")
enable_voice = st.sidebar.toggle("Enable Voice Alerts", value=True)
drift_sensitivity = st.sidebar.slider("Lane Sensitivity", 50, 150, 100)

voice_flag = "true" if enable_voice else "false"

# Use double {{ }} for all CSS/JS blocks to prevent f-string SyntaxErrors
JS_CODE = f"""
<div style="position: relative; width: 100%; max-width: 640px; margin: auto; border-radius: 20px; overflow: hidden; background: #000;">
    <video id="video" autoplay playsinline style="width: 100%; height: auto; display: block;"></video>
    <canvas id="output" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></canvas>
    
    <div id="signBox" style="position: absolute; top: 20px; right: 20px; width: 80px; height: 80px; background: rgba(255,255,255,0.9); border-radius: 50%; display: none; align-items: center; justify-content: center; border: 4px solid red; font-weight: bold; font-family: sans-serif; font-size: 12px; text-align: center; color: black;">
    </div>

    <div id="brakeAlert" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: rgba(255,0,0,0.85); color: white; padding: 20px 40px; border-radius: 10px; font-family: sans-serif; font-weight: bold; font-size: 24px; display: none; border: 5px solid white; z-index: 1000;">
        ⚠️ BRAKE: OBJECT DETECTED
    </div>

    <div id="overlay" style="position: absolute; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.9); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 100;">
        <h2 style="color: white; font-family: sans-serif;">ADAS PRO: RAHMAH EDITION</h2>
        <button id="startBtn" style="padding: 18px 40px; font-size: 20px; border-radius: 50px; background: #28a745; color: white; border: none; cursor: pointer;">START SYSTEM</button>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs"></script>
<script src="https://cdn.jsdelivr.net/npm/@tensorflow-models/coco-ssd"></script>

<script>
const video = document.getElementById('video');
const canvas = document.getElementById('output');
const ctx = canvas.getContext('2d', {{alpha: false, desynchronized: true}});
const brakeAlert = document.getElementById('brakeAlert');
const signBox = document.getElementById('signBox');

let model;
let lastSpeech = 0;
const synth = window.speechSynthesis;

function speak(text) {{
    if (!{voice_flag}) return;
    const now = Date.now();
    if (now - lastSpeech < 4000) return;
    synth.speak(new SpeechSynthesisUtterance(text));
    lastSpeech = now;
}}

async function start() {{
    model = await cocoSsd.load();
    const stream = await navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: 'environment' }} }});
    video.srcObject = stream;
    document.getElementById('overlay').style.display = 'none';
    speak("ADAS System Online");
    video.onloadedmetadata = () => render();
}}

async function render() {{
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);

    // 1. LANE TRACKING (Asari-Rashidi Pixel Logic)
    const h = canvas.height; const w = canvas.width;
    const roadTop = Math.floor(h * 0.7);
    const roadData = ctx.getImageData(0, roadTop, w, Math.floor(h * 0.3));
    const pixels = roadData.data;
    let leftDelt = 0, rightDelt = 0;

    for (let i = 0; i < pixels.length; i += 4) {{
        if (pixels[i] > 210 && pixels[i+1] > 210 && pixels[i+2] > 210) {{
            pixels[i]=0; pixels[i+1]=123; pixels[i+2]=255;
            let x = (i/4)%w;
            if (x < w*0.3) leftDelt++; if (x > w*0.7) rightDelt++;
        }}
    }
    ctx.putImageData(roadData, 0, roadTop);
    if(leftDelt > {drift_sensitivity}) speak("Check Left");
    if(rightDelt > {drift_sensitivity}) speak("Check Right");

    // 2. PCW & SIGN RECOGNITION (Run every few frames for battery)
    if (Date.now() % 5 == 0) {{
        const predictions = await model.detect(video);
        let collisionDetected = false;
        signBox.style.display = "none";

        predictions.forEach(p => {{
            // Collision Detection (Person/Car in center)
            if (["person", "car", "truck"].includes(p.class) && p.bbox[0] > w*0.25 && p.bbox[0] < w*0.75) {{
                collisionDetected = true;
            }}
            // Road Signs
            if (["stop sign", "traffic light"].includes(p.class)) {{
                signBox.style.display = "flex";
                signBox.innerText = p.class.toUpperCase();
            }}
        }});
        brakeAlert.style.display = collisionDetected ? "block" : "none";
        if(collisionDetected) speak("Brake");
    }}

    requestAnimationFrame(render);
}}
document.getElementById('startBtn').onclick = start;
</script>
"""

components.html(JS_CODE, height=650)

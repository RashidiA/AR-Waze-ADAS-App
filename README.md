# 🚗 ADAS Pro: Mobile Edge AI Vision System

An advanced **Advanced Driver Assistance System (ADAS)** designed specifically for mobile browsers. This project utilizes a **Heterogeneous Architecture** (combining Python/Streamlit with JavaScript/WebAssembly) to provide real-time safety analytics directly on the device, avoiding the latency of traditional server-side processing.

---

## 🔬 Learning Context
This application serves as a prototype for investigating **Computer Vision efficiency on Edge Devices**. It specifically targets:

* **Lane Departure Warning (LDW):** Real-time pixel-intensity mapping for white line tracking, visualized with **Blue AR Overlays**.
* **AR Navigation Logic:** Real-time directional guidance using floating 3D arrows anchored to the road environment.
* **Active Voice Safety:** Integrated **Web Speech API** for hands-free safety alerts and system status updates.
* **Road Sign Recognition:** Dynamic identification of regulatory signage such as Stop Signs and Traffic Lights.

---

## 🚀 Key Technical Features
* **Zero-Latency AR:** Employs `{desynchronized: true}` WebGL rendering to eliminate visual input lag.
* **Hybrid Execution:** Uses **Python** for the application interface and **JavaScript/WASM** for high-frequency (30 FPS) vision tasks.
* **Resource Optimized:** Implements a **Priority Queue** where lightweight tasks (Lane tracking) run every frame, while heavy AI inference runs every 7th frame to prevent device overheating.

---

## 🛠️ System Configuration

### 1. Python Requirements
To ensure the application runs correctly on the Streamlit server, you must create a file named `requirements.txt` in your main folder and include the following libraries:
* **Streamlit** (version 1.35.0 or higher) 
* **Requests** for weather data fetching
* **Pandas** and **Numpy** for data handling 
* **Pillow** for image processing compatibility 

### 2. Linux System Dependencies
Because the application processes video and graphics, the hosting server requires specific Linux-level headers. Create a file named `packages.txt` in your root directory and add the necessary graphics libraries (such as `freeglut3-dev`, `libgl1`, and `libpng-dev`) to allow the server to render the vision components correctly.

---

## 📖 Usage Instructions
1.  **Deployment:** Upload your source code to a GitHub repository and connect it to **Streamlit Cloud**.
2.  **Hardware Setup:** Mount your smartphone on a vehicle dashboard with a stable, unobstructed view of the area.
3.  **Initialization:** Open the provided URL in a mobile browser (Chrome or Safari) and tap the **"START SYSTEM"** button. You must grant **Camera**, **Location**, and **Audio** permissions for the AI to function.
4.  **Visual & Audio Indicators:**
    * **Blue Overlays:** Indicates that the system has successfully locked onto **White Road Lines**.
    * **Voice Alerts:** Announces "Warning: Drift Left/Right" if the vehicle leaves the lane center.
    * **Red "BRAKE" Alert:** Appears instantly if an object or person enters the central collision zone.
    * **Top-Right Indicator:** Displays recognized road signs and current weather/speed data.

---

## ⚖️ License (MIT)
**Copyright (c) 2026 Asari-Rashidi Energy Model Research Group**

This software is provided under the **MIT License**. This allows for free use, modification, and distribution, provided that the original copyright notice and this permission notice are included in all copies or substantial portions of the software. The software is provided "as is," without warranty of any kind.

---

## 📊 Developer & Academic Metadata
* **Core Model:** COCO-SSD (TensorFlow.js) 
* **Vision Engine:** Custom Pixel-Intensity Logic (White-Line Optimized) 
* **Lead Developer:** Asari Rashidi 
* **Application:** Real-world Road Testing 

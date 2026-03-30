# 🚗 ADAS Pro: Mobile Edge AI Vision System

[cite_start]An advanced **Advanced Driver Assistance System (ADAS)** designed specifically for mobile browsers[cite: 1]. [cite_start]This project utilizes a **Heterogeneous Architecture** (combining Python/Streamlit with JavaScript/WebAssembly) to provide real-time safety analytics directly on the device, avoiding the latency of traditional server-side processing[cite: 2].

---

## 🔬 Learning Context
[cite_start]This application serves as a prototype for investigating **Computer Vision efficiency on Edge Devices**[cite: 3]. It specifically targets:

* [cite_start]**Lane Departure Warning (LDW):** Real-time pixel-intensity mapping for white line tracking, visualized with **Blue AR Overlays**[cite: 4].
* **AR Navigation Logic:** Real-time directional guidance using floating 3D arrows anchored to the road environment.
* **Active Voice Safety:** Integrated **Web Speech API** for hands-free safety alerts and system status updates.
* [cite_start]**Road Sign Recognition:** Dynamic identification of regulatory signage such as Stop Signs and Traffic Lights[cite: 6].

---

## 🚀 Key Technical Features
* [cite_start]**Zero-Latency AR:** Employs `{desynchronized: true}` WebGL rendering to eliminate visual input lag[cite: 7].
* [cite_start]**Hybrid Execution:** Uses **Python** for the application interface and **JavaScript/WASM** for high-frequency (30 FPS) vision tasks[cite: 8].
* [cite_start]**Resource Optimized:** Implements a **Priority Queue** where lightweight tasks (Lane tracking) run every frame, while heavy AI inference runs every 7th frame to prevent device overheating[cite: 9].

---

## 🛠️ System Configuration

### 1. Python Requirements
[cite_start]To ensure the application runs correctly on the Streamlit server, you must create a file named `requirements.txt` in your main folder and include the following libraries[cite: 10]:
* [cite_start]**Streamlit** (version 1.35.0 or higher) [cite: 10]
* **Requests** for weather data fetching
* [cite_start]**Pandas** and **Numpy** for data handling [cite: 10]
* [cite_start]**Pillow** for image processing compatibility [cite: 10]

### 2. Linux System Dependencies
[cite_start]Because the application processes video and graphics, the hosting server requires specific Linux-level headers[cite: 11]. [cite_start]Create a file named `packages.txt` in your root directory and add the necessary graphics libraries (such as `freeglut3-dev`, `libgl1`, and `libpng-dev`) to allow the server to render the vision components correctly[cite: 11].

---

## 📖 Usage Instructions
1.  [cite_start]**Deployment:** Upload your source code to a GitHub repository and connect it to **Streamlit Cloud**[cite: 12].
2.  [cite_start]**Hardware Setup:** Mount your smartphone on a vehicle dashboard with a stable, unobstructed view of the area[cite: 13].
3.  [cite_start]**Initialization:** Open the provided URL in a mobile browser (Chrome or Safari) and tap the **"START SYSTEM"** button[cite: 14]. [cite_start]You must grant **Camera**, **Location**, and **Audio** permissions for the AI to function[cite: 15].
4.  **Visual & Audio Indicators:**
    * [cite_start]**Blue Overlays:** Indicates that the system has successfully locked onto **White Road Lines**[cite: 16].
    * **Voice Alerts:** Announces "Warning: Drift Left/Right" if the vehicle leaves the lane center.
    * [cite_start]**Red "BRAKE" Alert:** Appears instantly if an object or person enters the central collision zone[cite: 17].
    * [cite_start]**Top-Right Indicator:** Displays recognized road signs and current weather/speed data[cite: 18].

---

## ⚖️ License (MIT)
**Copyright (c) 2026 Asari-Rashidi Energy Model Research Group**

[cite_start]This software is provided under the **MIT License**[cite: 19]. [cite_start]This allows for free use, modification, and distribution, provided that the original copyright notice and this permission notice are included in all copies or substantial portions of the software[cite: 19]. [cite_start]The software is provided "as is," without warranty of any kind[cite: 20].

---

## 📊 Developer & Academic Metadata
* [cite_start]**Core Model:** COCO-SSD (TensorFlow.js) [cite: 21]
* [cite_start]**Vision Engine:** Custom Pixel-Intensity Logic (White-Line Optimized) [cite: 21]
* [cite_start]**Lead Developer:** Asari Rashidi [cite: 21]
* [cite_start]**Application:** Real-world Road Testing [cite: 21]
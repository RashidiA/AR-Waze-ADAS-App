# 🛡️ Privacy Policy: ADAS Pro Mobile Edge AI

This Privacy Policy outlines how the **ADAS Pro: Mobile Edge AI Vision System** handles data. As a research prototype developed by the **Asari-Rashidi Energy Model Research Group**, this application is designed with a "Privacy by Design" approach, ensuring that sensitive data remains under the user's control.

---

### 1. Data Collection & Processing Logic
Unlike traditional cloud-based systems, this application utilizes a **Heterogeneous Architecture** (Python/Streamlit and JavaScript/WebAssembly) to perform **Edge AI** processing. This means:
* **Local Execution:** All visual and spatial data is processed locally on your device's hardware.
* **No Data Transmission:** No video feeds, images, or precise location logs are transmitted to, stored on, or seen by our servers.

### 2. Hardware & Sensor Access
To provide active safety and navigation features, the app requires the following permissions:
* **Camera Access:** Required for real-time **Lane Departure Warning (LDW)** and **Object Detection**. The camera stream is used only for "in-memory" pixel analysis and is never recorded.
* **Location (GPS):** Required for calculating real-time vehicle speed and anchoring **AR Waze Navigation** markers.
* **Audio (Microphone/Speech):** Used exclusively for the **Web Speech API** to deliver hands-free voice alerts (e.g., "Brake" or "Drift Left").

### 3. Third-Party Integrations
* **TensorFlow.js:** The **COCO-SSD** model used for identifying pedestrians and road signs runs entirely within your mobile browser.
* **Streamlit Cloud:** The Python-based interface is hosted via Streamlit; however, the vision engine remains isolated within your local browser environment.

### 4. User Control
* **Permission Revocation:** You can revoke Camera, Location, or Audio access at any time through your browser's site settings.
* **Session-Based:** All data analysis is session-based. Once the browser tab is closed, all temporary processing data is cleared.

---

### 5. Contact & Metadata
* **Project:** ADAS Pro: Mobile Edge AI Vision System
* **Organization:** Asari-Rashidi Energy Model Research Group
* **Lead Developer:** Asari Rashidi
* **License:** MIT License
# 🧠 VIS-R: Vision-Language Robotic Perception System

VIS-R is a real-time **AI-powered robotic perception system** that combines **Computer Vision (YOLOv8)** with **Vision-Language Models (LLaVA / Moondream)** and **speech interfaces** to enable intelligent scene understanding and human–robot interaction.

It is designed as a **modular robotics AI pipeline** for future integration with **ROS 2, edge devices, and autonomous robots**.

---

## 🚀 Key Features

- 🎯 Real-time object detection using **YOLOv8**
- 🧠 Vision-Language reasoning (LLaVA / Moondream / Gemini-ready architecture)
- 🗣️ Speech-to-Text (STT) interactive input
- 🔊 Text-to-Speech (TTS) responses
- ⚡ Fast + Deep dual-stage VLM inference pipeline
- 📊 Rule-based decision engine for robotics actions
- 🖥️ Live UI dashboard with alerts & detection overlays
- 📸 Snapshot capture system
- 🧩 Modular architecture for easy scaling

---

---
## 🏗️ System Architecture

```text
Camera Input
     │
     ▼
YOLOv8 Object Detection
     │
     ▼
Frame + Detections
     │
     ▼
VLM Client (Gemini / LLaVA / Moondream)
     │
     ├── Fast Mode
     └── Deep Mode
     │
     ▼
Parser Layer
     │
     ▼
Rule Engine
     │
     ├── Text Output
     ├── Voice Output
     └── UI Alerts
```

```

---

## 📁 Project Structure

```text
VIS-R/
│
├── src/
│   ├── camera.py
│   ├── vision.py
│   ├── vlm_client.py
│   ├── parser.py
│   ├── automation.py
│   ├── tts.py
│   ├── stt.py
│   ├── ui.py
│   ├── logger.py
│
├── main.py
├── config.py
├── requirements.txt
└── README.md
```

---
## 📸 Output Sample

<b>Output Sample</b><br>

<p align="center">
  <img src="assets/VSIR.png" width="700"/>
</p>
---
🔮 Use Cases
🤖 Robotics perception systems

🏭 Industrial monitoring

🧑‍🤝‍🧑 Human–robot interaction

🎥 Smart surveillance systems

🧠 Edge AI assistants

🚗 Autonomous systems research

🛣️ Future Roadmap
ROS 2 integration 🤖

Multi-camera fusion system 📷

Edge deployment (Raspberry Pi 5 / Jetson Nano)

Voice-controlled robot actions 🗣️

Reinforcement learning-based navigation

Real-time object tracking + memory system

👨‍💻 Author
Harsh Yadav
AI • Robotics • Computer Vision • Embedded Systems

GitHub: https://github.com/Harsh-Y99

⭐ Status
🚧 Actively under development
🧠 Research + Robotics + AI Fusion Project

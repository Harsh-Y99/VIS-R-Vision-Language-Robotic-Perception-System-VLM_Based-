# VIS-R: Vision-Language Robotic Perception System

## Overview

VIS-R is an intelligent robotic perception system that combines Computer Vision, Vision-Language Models (VLMs), and speech interfaces to enable real-time scene understanding and human-robot interaction.

The system integrates YOLOv8 object detection with multimodal AI models such as LLaVA and Moondream, allowing users to query their environment using natural language and receive contextual responses. The architecture is designed with future ROS 2 and robotics integration in mind.

---

## Features

* Real-time object detection using YOLOv8
* Vision-Language reasoning with LLaVA and Moondream
* Natural language scene understanding
* Speech-to-Text (STT) input pipeline
* Text-to-Speech (TTS) response generation
* Multi-model AI backend selection
* Modular and extensible architecture
* Robotics-oriented design for future ROS 2 integration

---

## Tech Stack

### Languages

* Python

### Computer Vision

* OpenCV
* YOLOv8

### Vision-Language Models

* LLaVA
* Moondream

### AI & Automation

* Gemini API
* Speech Recognition
* Text-to-Speech

### Frameworks & Tools

* Flask
* Git
* Linux

---

## System Architecture

```text
Camera/Input
      │
      ▼
   YOLOv8
      │
      ▼
 Scene Analysis
      │
      ▼
 VLM (LLaVA/Moondream)
      │
      ▼
 Natural Language Reasoning
      │
      ├── Text Response
      └── Voice Response (TTS)
```

---

## Project Structure

```text
VIS-R/
├── src/
├── main.py
├── config.py
├── requirements.txt
├── README.md
└── assets/
```

---

## Use Cases

* Intelligent robotic perception
* Human-robot interaction
* Context-aware AI assistants
* Smart surveillance systems
* Assistive robotics
* Edge AI experimentation

---

## Current Status

🚧 Under Active Development

Current focus:

* Dashboard improvements
* Performance optimization
* Enhanced VLM reasoning
* Future ROS 2 integration

---

## Future Roadmap

* ROS 2 integration
* Robot navigation support
* Multi-camera perception
* Voice-controlled robotics
* Edge deployment on Raspberry Pi 5
* Autonomous task execution

---

## Author

**Harsh Yadav**

AI • Robotics • Computer Vision • Embedded Systems

GitHub: https://github.com/Harsh-Y99

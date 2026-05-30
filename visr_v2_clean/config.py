import os

# ─────────────────────────────────────────────
#  VIS-R v2 — Configuration
# ─────────────────────────────────────────────

# Camera
CAMERA_INDEX = 0
FRAME_WIDTH  = 1280
FRAME_HEIGHT = 720

# YOLO
YOLO_MODEL      = 'yolov8n.pt'
YOLO_CONFIDENCE = 0.45
YOLO_TRACK      = True

# VLM / Ollama
OLLAMA_HOST      = 'http://localhost:11434'
MOONDREAM_MODEL  = 'moondream'
LLAVA_MODEL      = 'llava'
VLM_TIMEOUT      = 20
VLM_FAST_INTERVAL  = 10
VLM_DEEP_INTERVAL  = 60

# Prompts
DEEP_PROMPT = """You are an intelligent vision system for a robotics application.

Carefully analyze the given camera scene step-by-step:
1. Identify all visible objects (static and moving).
2. Detect people, their actions, and interactions.
3. Understand the environment context (indoor/outdoor, road, lab, etc.).
4. Check for safety hazards, unusual behavior, or anomalies.

Focus on:
- Human safety
- Motion risks (fall, collision, fire, sharp objects, etc.)
- Unexpected or abnormal situations

If uncertain, make the best possible inference based on visual evidence.

Respond STRICTLY in this format (no extra text, no explanations):

RISK_LEVEL: LOW | MEDIUM | HIGH
DESCRIPTION: <one precise sentence describing the scene and risk>
SUGGESTED_ACTION: <one clear, actionable step for a robot or human>"""

FAST_PROMPT = "Describe this scene in one sentence. Is there any risk? Answer YES or NO at the end."

# Rule Engine
RISK_RULES = {
    'HIGH':   {'action': 'alert',   'speak': True,  'log': True,  'color': (0, 0, 255)},
    'MEDIUM': {'action': 'warning', 'speak': True,  'log': True,  'color': (0, 140, 255)},
    'LOW':    {'action': 'none',    'speak': False, 'log': False, 'color': (0, 255, 120)},
}

# Voice / TTS  — Indian English accent via gTTS
TTS_LANGUAGE       = 'en-in'
TTS_HINDI_LANGUAGE = 'hi'
TTS_ENABLED        = True
VOICE_GREET        = "V-I-S-R system online. Vision Intelligence System for Robotics, ready."

# STT
STT_ENABLED    = True
STT_TIMEOUT    = 5
STT_PHRASE_LIMIT = 8

# Logging
DB_PATH    = os.path.join('data', 'logs.db')
FRAMES_DIR = os.path.join('data', 'frames')
os.makedirs(FRAMES_DIR, exist_ok=True)

# UI
UI_WIDTH  = 1280
UI_HEIGHT = 720

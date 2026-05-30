# VIS-R v2 — Vision Intelligence System · Robotics

Dark terminal robotics HUD · YOLOv8 · Moondream2 · LLaVA · Indian Voice

## What's New in v2

| Feature | v1 | v2 |
|---|---|---|
| UI Input | Console only | **In-HUD keyboard typing** |
| Voice Output | gTTS (generic English) | **gTTS Indian English (en-in)** |
| Voice Input | None | **SpeechRecognition (en-IN)** |
| Risk panel | Static bar | **Animated pulsing (HIGH alert glow)** |
| Detection boxes | Basic rect | **Corner marks + track trails** |
| Alerts | None | **Slide-in overlay alerts** |
| Snapshots | None | **[S] key saves frame** |
| Frame smoothing | Resize only | **Linear interp + contrast boost** |
| TTS spam | Every event | **8s cooldown per risk level** |
| STT status | None | **Mic indicator + voice bars** |

## Keyboard Controls

| Key | Action |
|-----|--------|
| `T` | Type a query in the HUD input bar |
| `V` | Voice input (speak your query) |
| `ENTER` | Submit typed query |
| `ESC` | Cancel typing |
| `S` | Save snapshot to `data/frames/` |
| `R` | Reset risk / VLM state |
| `Q` | Quit |

## Setup

```bash
pip install -r requirements.txt

# Install Ollama models
ollama pull moondream
ollama pull llava      # optional, for deep reasoning
```

## Run

```bash
cd visr_v2
python main.py
```

## Voice Notes

- TTS uses **gTTS `en-in`** — Indian English accent (requires internet)
- Offline fallback: `pyttsx3` (neutral voice)
- STT uses **Google Web Speech `en-IN`** — recognises Indian accented English
- Voice alerts have **8 second cooldown** to prevent spam

## Architecture

```
Camera → VisionDetector (YOLOv8) → UI (OpenCV HUD)
                                ↓
                        VLMClient (Moondream2 / LLaVA via Ollama)
                                ↓
                        RuleEngine → TTSManager (gTTS en-in)
                                   → DatabaseLogger (SQLite)
STTManager ← [V key] ──────────────────────────────────────────
```

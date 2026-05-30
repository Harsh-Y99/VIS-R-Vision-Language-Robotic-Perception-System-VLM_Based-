"""
VIS-R v2 — Main Entry Point
Vision Intelligence System for Robotics
"""
import cv2
import time
import threading
import datetime
import os

from src.camera    import Camera
from src.vision    import VisionDetector
from src.vlm_client import VLMClient
from src.parser    import parse_vlm_response, parse_fast_response
from src.automation import RuleEngine
from src.tts       import TTSManager
from src.stt       import STTManager
from src.logger    import DatabaseLogger
from src.ui        import UI
from config import (
    FRAME_WIDTH, FRAME_HEIGHT, VLM_FAST_INTERVAL, VLM_DEEP_INTERVAL,
    VOICE_GREET, FRAMES_DIR
)


def main():
    print("=" * 60)
    print("  VIS-R v2  |  Vision Intelligence System · Robotics")
    print("=" * 60)

    # ── Init components ───────────────────────────────────────
    camera   = Camera(index=0, width=FRAME_WIDTH, height=FRAME_HEIGHT)
    detector = VisionDetector()
    vlm      = VLMClient(fast_interval=VLM_FAST_INTERVAL, deep_interval=VLM_DEEP_INTERVAL)
    tts      = TTSManager()
    stt      = STTManager()
    logger   = DatabaseLogger()
    rule_eng = RuleEngine(tts, logger)
    ui       = UI(width=FRAME_WIDTH, height=FRAME_HEIGHT)

    vlm.start()

    # Greeting
    tts.speak(VOICE_GREET)

    # ── State ─────────────────────────────────────────────────
    frame_count          = 0
    last_vlm_frame       = None
    vlm_response         = "Vision pipeline initialising..."
    current_risk         = "LOW"
    deep_response_ready  = False

    # ── Custom query thread ───────────────────────────────────
    def handle_queries():
        nonlocal vlm_response, deep_response_ready, last_vlm_frame
        while True:
            query = ui.user_query_queue.get()
            if query and last_vlm_frame is not None:
                print(f"[Query] {query}")
                tts.speak(f"Processing your query: {query}")
                vlm.deep_queue.put(last_vlm_frame.copy())

    threading.Thread(target=handle_queries, daemon=True).start()

    # ── STT thread ────────────────────────────────────────────
    def handle_stt():
        nonlocal vlm_response, last_vlm_frame
        while True:
            result = stt.get_result()
            if result:
                ui.set_stt_status("")
                ui.stt_active = False
                print(f"[Voice] {result}")
                tts.speak(f"You said: {result}. Processing now.")
                ui.user_query_queue.put(result)
                ui.push_alert(f"Voice: {result[:50]}", duration=4.0)
            time.sleep(0.1)

    threading.Thread(target=handle_stt, daemon=True).start()

    print("[VIS-R] Running. Press [T] to type, [V] for voice, [Q] to quit.")
    print()

    # ── Main loop ─────────────────────────────────────────────
    while True:
        frame = camera.get_frame()
        if frame is None:
            print("[Camera] No frame — retrying...")
            time.sleep(0.05)
            continue

        ui.fps = camera.fps

        # YOLO detection/tracking
        annotated, detections = detector.process_frame(frame)

        # Keep reference for VLM queries
        if frame_count % 5 == 0:
            last_vlm_frame = frame.copy()

        # Submit to VLM
        vlm.submit_frame(frame)

        # ── VLM results ───────────────────────────────────────
        try:
            result_type, response, ts = vlm.result_queue.get_nowait()

            if result_type == 'deep' and response:
                parsed       = parse_vlm_response(response)
                current_risk = parsed['risk_level']
                desc         = parsed['description']
                act          = parsed['suggested_action']
                vlm_response = f"[DEEP]  Risk: {current_risk}  |  {desc}  |  Action: {act}"
                rule_eng.evaluate(current_risk, desc, act, frame)
                deep_response_ready = True

                if current_risk in ('HIGH', 'MEDIUM'):
                    ui.push_alert(
                        f"{current_risk}: {desc[:60]}",
                        duration=5.0,
                        color=(50,50,230) if current_risk=='HIGH' else (0,140,255)
                    )

            elif result_type == 'fast' and response and not deep_response_ready:
                fast = parse_fast_response(response)
                current_risk = "MEDIUM" if fast['risk_flag'] else "LOW"
                vlm_response = f"[FAST]  {fast['description'][:120]}"

        except Exception:
            pass

        # ── UI update ─────────────────────────────────────────
        action = ui.update(annotated, detections, current_risk, vlm_response)

        if action == 'quit':
            break

        elif action == 'voice':
            if not stt.is_listening():
                ui.stt_active = True
                ui.set_stt_status("Listening...")
                ui.push_alert("Voice activated — speak now", duration=3.0, color=(0,200,255))
                tts.speak("Listening. Please speak your query.")
                stt.listen_once()
            else:
                ui.push_alert("Already listening...", duration=2.0)

        elif action == 'snapshot':
            ts_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path   = os.path.join(FRAMES_DIR, f"snapshot_{ts_str}.jpg")
            cv2.imwrite(path, frame)
            ui.push_alert(f"Snapshot saved: {path}", duration=3.0, color=(0,200,100))
            tts.speak("Snapshot saved.")

        elif action == 'reset':
            current_risk        = "LOW"
            vlm_response        = "System reset."
            deep_response_ready = False
            ui.push_alert("System reset.", duration=2.0)

        # STT status sync
        if stt.is_listening():
            ui.set_stt_status("Listening...")
            ui.stt_active = True
        else:
            if ui.stt_active:
                ui.set_stt_status("Processing...")
            # will be cleared by stt thread when result arrives

        frame_count += 1

    # ── Cleanup ───────────────────────────────────────────────
    print("[VIS-R] Shutting down...")
    tts.speak("V I S R shutting down. Goodbye.")
    time.sleep(1.5)
    vlm.stop()
    camera.release()
    ui.close()
    logger.close()
    print("[VIS-R] Done.")


if __name__ == '__main__':
    main()

"""
VIS-R v2 — Speech-to-Text (STT)
Uses SpeechRecognition + Google Web Speech API.
Runs in a background thread, puts recognised text into a queue.
"""
import threading, queue, time

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

from config import STT_ENABLED, STT_TIMEOUT, STT_PHRASE_LIMIT


class STTManager:
    def __init__(self):
        self.enabled   = STT_ENABLED and SR_AVAILABLE
        self.result_q  = queue.Queue()
        self._listening = False
        self._thread   = None

        if self.enabled:
            self._recognizer = sr.Recognizer()
            self._recognizer.energy_threshold = 300
            self._recognizer.dynamic_energy_threshold = True
            print("[STT] SpeechRecognition ready.")
        else:
            if not SR_AVAILABLE:
                print("[STT] SpeechRecognition not installed — voice input disabled.")
            else:
                print("[STT] STT disabled in config.")

    def listen_once(self):
        """Non-blocking: starts a single listen attempt in background."""
        if not self.enabled or self._listening:
            return
        self._thread = threading.Thread(target=self._listen_worker, daemon=True)
        self._thread.start()

    def _listen_worker(self):
        self._listening = True
        try:
            with sr.Microphone() as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = self._recognizer.listen(
                    source,
                    timeout=STT_TIMEOUT,
                    phrase_time_limit=STT_PHRASE_LIMIT
                )
            text = self._recognizer.recognize_google(audio, language="en-IN")
            self.result_q.put(text.strip())
            print(f"[STT] Recognised: {text}")
        except sr.WaitTimeoutError:
            print("[STT] No speech detected (timeout).")
        except sr.UnknownValueError:
            print("[STT] Could not understand audio.")
        except Exception as e:
            print(f"[STT] Error: {e}")
        finally:
            self._listening = False

    def is_listening(self):
        return self._listening

    def get_result(self):
        """Non-blocking. Returns text string or None."""
        try:
            return self.result_q.get_nowait()
        except queue.Empty:
            return None

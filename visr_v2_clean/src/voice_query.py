"""
VIS-R Voice Query — Speech-to-Text using Google STT (Indian English)
Requires: pip install SpeechRecognition pyaudio
Falls back gracefully if not available.
"""

import threading
import queue

try:
    import speech_recognition as sr
    STT_AVAILABLE = True
except ImportError:
    STT_AVAILABLE = False


class VoiceQuery:
    """
    Non-blocking microphone listener.
    Calls callback(text) when speech is recognized.
    """

    def __init__(self, language="en-IN", timeout=5):
        self.language  = language
        self.timeout   = timeout
        self.available = STT_AVAILABLE
        self._result_q = queue.Queue()

        if STT_AVAILABLE:
            self._recognizer = sr.Recognizer()
            self._recognizer.pause_threshold  = 0.8
            self._recognizer.energy_threshold = 300
            print(f"[STT] Voice query ready | lang={language}")
        else:
            print("[STT] SpeechRecognition not installed — voice query disabled")
            print("      Install: pip install SpeechRecognition pyaudio")

    def listen_once(self, callback=None):
        """Start a one-shot listen in background thread."""
        if not self.available:
            return
        def _listen():
            try:
                with sr.Microphone() as src:
                    self._recognizer.adjust_for_ambient_noise(src, duration=0.5)
                    print("[STT] Listening...")
                    audio = self._recognizer.listen(src, timeout=self.timeout,
                                                    phrase_time_limit=8)
                text = self._recognizer.recognize_google(
                    audio, language=self.language
                )
                print(f"[STT] Heard: {text}")
                self._result_q.put(text)
                if callback:
                    callback(text)
            except sr.WaitTimeoutError:
                print("[STT] No speech detected")
            except sr.UnknownValueError:
                print("[STT] Could not understand audio")
            except Exception as e:
                print(f"[STT] Error: {e}")

        threading.Thread(target=_listen, daemon=True).start()

    def get_result(self):
        """Non-blocking poll for STT result."""
        try:
            return self._result_q.get_nowait()
        except queue.Empty:
            return None

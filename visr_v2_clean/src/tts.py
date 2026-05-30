"""
VIS-R v2 — TTS Manager
Indian English accent (en-in) via gTTS online,
pyttsx3 offline fallback, Hindi auto-detect.
Non-blocking threaded playback.
"""
import socket, re, threading, queue, time, io
import pyttsx3
from gtts import gTTS
import pygame

from config import TTS_LANGUAGE, TTS_HINDI_LANGUAGE, TTS_ENABLED


class TTSManager:
    def __init__(self):
        self._enabled  = TTS_ENABLED
        self._online   = self._check_internet()
        self._engine   = None
        self._queue    = queue.Queue()
        self._lock     = threading.Lock()
        self._speaking = False

        if not self._online:
            try:
                self._engine = pyttsx3.init()
                # Try to set a female Indian voice if available
                for v in self._engine.getProperty('voices'):
                    if 'india' in v.name.lower() or 'hindi' in v.name.lower():
                        self._engine.setProperty('voice', v.id)
                        break
                self._engine.setProperty('rate', 165)
            except Exception:
                pass

        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        except Exception:
            pass

        threading.Thread(target=self._worker, daemon=True).start()

    # ── Helpers ────────────────────────────────────────────────
    def _check_internet(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except OSError:
            return False

    def _is_hindi(self, text):
        return bool(re.search(r'[\u0900-\u097F]', text))

    # ── Public API ────────────────────────────────────────────
    def speak(self, text: str, priority: bool = False):
        """Queue text for speech. priority=True clears queue first."""
        if not self._enabled or not text:
            return
        if priority:
            while not self._queue.empty():
                try: self._queue.get_nowait()
                except queue.Empty: break
        self._queue.put(text)

    def is_speaking(self):
        return self._speaking

    def stop(self):
        while not self._queue.empty():
            try: self._queue.get_nowait()
            except queue.Empty: break
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

    # ── Worker ────────────────────────────────────────────────
    def _worker(self):
        while True:
            text = self._queue.get()
            self._speaking = True
            try:
                if self._online:
                    self._speak_online(text)
                elif self._engine:
                    self._speak_offline(text)
            except Exception as e:
                print(f"[TTS] Error: {e}")
            finally:
                self._speaking = False

    def _speak_online(self, text):
        lang = TTS_HINDI_LANGUAGE if self._is_hindi(text) else TTS_LANGUAGE
        tts  = gTTS(text=text, lang=lang, slow=False)
        fp   = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        try:
            pygame.mixer.music.load(fp)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
        except Exception as e:
            print(f"[TTS] Playback error: {e}")

    def _speak_offline(self, text):
        if self._is_hindi(text):
            text = "Hindi input received. " + text
        with self._lock:
            self._engine.say(text)
            self._engine.runAndWait()

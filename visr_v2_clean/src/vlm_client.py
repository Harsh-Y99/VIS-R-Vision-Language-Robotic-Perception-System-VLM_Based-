import threading
import queue
import time
import requests
import base64
import cv2
from config import OLLAMA_HOST, MOONDREAM_MODEL, LLAVA_MODEL, DEEP_PROMPT, FAST_PROMPT, VLM_TIMEOUT

class VLMClient:
    """Hybrid VLM client: Moondream2 for fast, LLaVA for deep reasoning."""
    def __init__(self, fast_interval=5, deep_interval=30):
        self.fast_interval = fast_interval
        self.deep_interval = deep_interval
        self.ollama_url = f"{OLLAMA_HOST}/api/generate"
        self.fast_queue = queue.Queue()
        self.deep_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.running = False
        self.thread = None
        self.frame_counter = 0

    def _encode_frame(self, frame):
        _, buffer = cv2.imencode('.jpg', frame)
        return base64.b64encode(buffer).decode('utf-8')

    def _quick_caption(self, frame):
        img_b64 = self._encode_frame(frame)
        payload = {
            "model": MOONDREAM_MODEL,
            "prompt": FAST_PROMPT,
            "images": [img_b64],
            "stream": False
        }
        try:
            resp = requests.post(self.ollama_url, json=payload, timeout=VLM_TIMEOUT)
            return resp.json().get('response', '')
        except Exception as e:
            print(f"[VLM] Fast reasoning error: {e}")
            return ""

    def _deep_reason(self, frame):
        img_b64 = self._encode_frame(frame)
        payload = {
            "model": LLAVA_MODEL,
            "prompt": DEEP_PROMPT,
            "images": [img_b64],
            "stream": False
        }
        try:
            resp = requests.post(self.ollama_url, json=payload, timeout=VLM_TIMEOUT)
            return resp.json().get('response', '')
        except Exception as e:
            print(f"[VLM] Deep reasoning error: {e}")
            return ""

    def _worker(self):
        while self.running:
            # Process fast requests
            try:
                frame = self.fast_queue.get(timeout=0.1)
                fast_response = self._quick_caption(frame)
                self.result_queue.put(('fast', fast_response, time.time()))
                # If fast response indicates risk, schedule deep analysis on same frame
                if "YES" in fast_response.upper():
                    self.deep_queue.put(frame)
            except queue.Empty:
                pass

            # Process deep requests
            try:
                frame = self.deep_queue.get(timeout=0.1)
                deep_response = self._deep_reason(frame)
                self.result_queue.put(('deep', deep_response, time.time()))
            except queue.Empty:
                pass

            time.sleep(0.05)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)

    def submit_frame(self, frame):
        self.frame_counter += 1
        # Fast path every fast_interval frames
        if self.frame_counter % self.fast_interval == 0:
            self.fast_queue.put(frame.copy())
        # Deep path every deep_interval frames
        if self.frame_counter % self.deep_interval == 0:
            self.deep_queue.put(frame.copy())
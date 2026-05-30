import cv2
import time

class Camera:
    """Webcam capture with FPS calculation."""
    def __init__(self, index=0, width=640, height=480):
        self.cap = cv2.VideoCapture(index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.fps = 0
        self.last_time = time.time()
        self.frame_count = 0

    def get_frame(self):
        ret, frame = self.cap.read()
        if ret:
            self.frame_count += 1
            now = time.time()
            if now - self.last_time >= 1.0:
                self.fps = self.frame_count
                self.frame_count = 0
                self.last_time = now
            return frame
        return None

    def release(self):
        self.cap.release()
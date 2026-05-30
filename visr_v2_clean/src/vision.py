"""
VIS-R v2 — Vision Detector
YOLOv8 tracking + normalised detection output.
"""
from ultralytics import YOLO
from config import YOLO_MODEL, YOLO_CONFIDENCE, YOLO_TRACK


class VisionDetector:
    def __init__(self, model_path=YOLO_MODEL, conf=YOLO_CONFIDENCE, track=YOLO_TRACK):
        self.model = YOLO(model_path)
        self.conf  = conf
        self.track = track
        self._orig_w = 640
        self._orig_h = 480

    def process_frame(self, frame):
        h, w = frame.shape[:2]
        self._orig_w, self._orig_h = w, h

        if self.track:
            results = self.model.track(frame, persist=True, conf=self.conf, verbose=False)
        else:
            results = self.model(frame, conf=self.conf, verbose=False)

        annotated  = results[0].plot()
        detections = []
        boxes      = results[0].boxes

        if boxes is not None:
            for box in boxes:
                cls    = int(box.cls[0])
                conf   = float(box.conf[0])
                bbox   = box.xyxy[0].tolist()   # x1,y1,x2,y2 absolute
                tid    = int(box.id[0]) if box.id is not None else None
                label  = self.model.names[cls]
                detections.append({
                    'class_name': label,
                    'label':      label,
                    'confidence': conf,
                    'conf':       conf,
                    'bbox':       bbox,
                    'track_id':   tid,
                })

        return annotated, detections

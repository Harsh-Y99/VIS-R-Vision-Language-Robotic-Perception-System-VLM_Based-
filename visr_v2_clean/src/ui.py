"""
VIS-R v2 — HUD UI
Dark terminal / robotics aesthetic.
Smooth camera feed, interactive query input, animated alerts,
scan-line overlay, animated risk bars, detection panel with tracks.
"""
import cv2, time, queue, threading, math
import numpy as np

# ── Palette (BGR) ──────────────────────────────────────────────
C = {
    'bg':           (10,  20,  14),
    'panel':        (6,   14,  10),
    'panel_alt':    (8,   18,  13),
    'border':       (20,  55,  35),
    'border_bright':(35,  90,  55),
    'green':        (0,   255, 130),
    'green_dim':    (0,   120,  55),
    'green_dark':   (0,    55,  20),
    'cyan':         (220, 240,  50),   # yellow-green
    'amber':        (0,   200, 255),   # BGR amber
    'orange':       (30,  130, 255),
    'red':          (50,   50, 230),
    'red_bright':   (30,   30, 255),
    'text':         (170, 210, 180),
    'text_dim':     (60,  110,  80),
    'text_bright':  (220, 245, 225),
    'white':        (230, 240, 235),
    'input_bg':     (5,   25,  15),
    'input_cursor': (0,   255, 130),
}

RISK_COLOR = {
    'LOW':    C['green'],
    'MEDIUM': C['amber'],
    'HIGH':   C['red_bright'],
}
RISK_FILL = {'LOW': 0.15, 'MEDIUM': 0.52, 'HIGH': 0.92}
RISK_GLOW  = {'LOW': C['green_dark'], 'MEDIUM': (0,60,80), 'HIGH': (30,10,60)}

DET_COLORS = {
    'person':   C['cyan'],
    'car':      C['amber'],
    'bicycle':  C['orange'],
    'default':  C['green'],
}

FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_M = cv2.FONT_HERSHEY_DUPLEX


# ── Helpers ────────────────────────────────────────────────────
def _put(frame, text, pos, scale=0.42, color=None, thick=1, font=FONT):
    color = color or C['text']
    cv2.putText(frame, str(text), pos, font, scale, color, thick, cv2.LINE_AA)

def _rect(frame, x, y, w, h, color, fill=-1):
    cv2.rectangle(frame, (x, y), (x+w, y+h), color, fill)

def _hline(frame, y, x1, x2, color=None, thick=1):
    cv2.line(frame, (x1, y), (x2, y), color or C['border'], thick)

def _vline(frame, x, y1, y2, color=None, thick=1):
    cv2.line(frame, (x, y1), (x, y2), color or C['border'], thick)

def _alpha_rect(frame, x, y, w, h, color, alpha):
    sub  = frame[y:y+h, x:x+w]
    ovl  = np.full_like(sub, color[::-1] if len(color)==3 else color)
    cv2.addWeighted(ovl, alpha, sub, 1-alpha, 0, sub)
    frame[y:y+h, x:x+w] = sub

def _corner_marks(frame, x, y, w, h, color, size=12, thick=2):
    corners = [(x,y),(x+w,y),(x,y+h),(x+w,y+h)]
    dirs    = [(1,1),(-1,1),(1,-1),(-1,-1)]
    for (px,py),(dx,dy) in zip(corners, dirs):
        cv2.line(frame,(px,py),(px+dx*size,py), color, thick, cv2.LINE_AA)
        cv2.line(frame,(px,py),(px,py+dy*size), color, thick, cv2.LINE_AA)

def _wrap_text(text, max_w, scale, thick=1):
    """Word-wrap text to fit max_w pixels wide."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        (tw,_),_ = cv2.getTextSize(test, FONT, scale, thick)
        if tw > max_w and cur:
            lines.append(cur)
            cur = w
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines


# ── Main UI Class ──────────────────────────────────────────────
class UI:
    def __init__(self, width=1280, height=720):
        self.W, self.H = width, height
        self.window_name = "VIS-R  ·  VISION INTELLIGENCE SYSTEM  ·  ROBOTICS  v2"

        # State
        self.fps         = 0.0
        self.risk_level  = "LOW"
        self.vlm_text    = "Initialising vision pipeline..."
        self.detections  = []
        self.stt_active  = False
        self.stt_status  = ""          # "Listening...", "Processing...", etc.

        # Query input state
        self.user_query_queue = queue.Queue()
        self._input_text   = ""
        self._input_active = False
        self._input_blink  = True
        self._blink_t      = time.time()

        # Alerts / notifications
        self._alerts      = []   # list of (msg, expire_time, color)

        # Timing
        self._start_time  = time.time()
        self._frame_times = []
        self._scan_phase  = 0.0
        self._pulse_phase = 0.0
        self._last_render = time.time()

        # Track history for trail effect
        self._track_history = {}   # track_id -> [(cx,cy), ...]

        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, self.W, self.H)
        cv2.setMouseCallback(self.window_name, self._mouse_cb)

        # Keyboard input thread (console fallback)
        threading.Thread(target=self._console_input_thread, daemon=True).start()

    # ── Input ─────────────────────────────────────────────────
    def _console_input_thread(self):
        while True:
            q = input()
            if q.strip():
                self.user_query_queue.put(q.strip())

    def _mouse_cb(self, event, x, y, flags, param):
        pass  # future: clickable regions

    def push_alert(self, msg, duration=4.0, color=None):
        color = color or C['amber']
        expire = time.time() + duration
        self._alerts = [(m,e,c) for m,e,c in self._alerts if time.time()<e]
        self._alerts.append((msg, expire, color))

    def set_stt_status(self, status: str):
        self.stt_status = status

    # ── Uptime ────────────────────────────────────────────────
    def _uptime(self):
        s = int(time.time() - self._start_time)
        return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}"

    # ── Scanline Overlay ──────────────────────────────────────
    def _draw_scanlines(self, canvas, x, y, w, h, alpha=0.08):
        for gy in range(y, y+h, 4):
            sub = canvas[gy:gy+1, x:x+w]
            dark = (sub * (1-alpha)).astype(np.uint8)
            canvas[gy:gy+1, x:x+w] = dark

    # ── Moving scan bar ───────────────────────────────────────
    def _draw_scan_bar(self, canvas, vx, vy, vw, vh):
        bar_y = vy + int(vh * (self._scan_phase % 1.0))
        _alpha_rect(canvas, vx, bar_y, vw, 3, (50,160,80), 0.35)

    # ── Header ────────────────────────────────────────────────
    def _draw_header(self, canvas):
        H, W = 44, self.W
        _alpha_rect(canvas, 0, 0, W, H, (6,14,10), 0.95)
        _hline(canvas, H, 0, W, C['border_bright'], 1)

        # Logo
        _put(canvas, "VIS-R", (14, 18), scale=0.60, color=C['green'], thick=2, font=FONT_M)
        _put(canvas, "VISION INTELLIGENCE SYSTEM  ·  ROBOTICS  v2",
             (88, 18), scale=0.34, color=C['text_dim'])
        _put(canvas, "POWERED BY YOLO + MOONDREAM2",
             (88, 36), scale=0.28, color=C['green_dark'])

        # Right metrics
        pulse = abs(math.sin(self._pulse_phase * 3)) 
        dot_color = tuple(int(c * (0.5 + 0.5*pulse)) for c in C['green'])
        cv2.circle(canvas, (W-12, 22), 5, dot_color, -1)

        metrics = [
            (f"{self.fps:.0f}", "FPS"),
            (self._uptime(),    "UPTIME"),
            (self.risk_level,   "RISK"),
        ]
        x = W - 28
        for val, lbl in reversed(metrics):
            col = RISK_COLOR.get(val, C['green']) if lbl == "RISK" else C['green']
            (tw,_),_ = cv2.getTextSize(val, FONT, 0.50, 1)
            _put(canvas, val, (x-tw, 20), scale=0.50, color=col, thick=1)
            (lw,_),_ = cv2.getTextSize(lbl, FONT, 0.28, 1)
            _put(canvas, lbl, (x-lw, 38), scale=0.28, color=C['text_dim'])
            x -= max(tw, lw) + 26

        # STT indicator
        if self.stt_active or self.stt_status:
            mic_col = C['red_bright'] if self.stt_active else C['text_dim']
            cv2.circle(canvas, (W//2, 22), 6, mic_col, -1 if self.stt_active else 1)
            _put(canvas, self.stt_status or "MIC", (W//2+10, 26), scale=0.30, color=mic_col)

    # ── Side Panel background ──────────────────────────────────
    def _draw_side_bg(self, canvas, sx, sy, sw, sh):
        _alpha_rect(canvas, sx, sy, sw, sh, (6,14,10), 0.92)
        _vline(canvas, sx, sy, sy+sh, C['border_bright'], 1)

    # ── Risk Panel ────────────────────────────────────────────
    def _draw_risk_panel(self, canvas, x, y, w, h):
        _rect(canvas, x, y, w, h, C['panel'], -1)
        _rect(canvas, x, y, w, h, C['border'], 1)

        _put(canvas, "RISK ASSESSMENT", (x+8, y+13), scale=0.30, color=C['text_dim'])
        _hline(canvas, y+17, x, x+w, C['border'])

        risk_col = RISK_COLOR.get(self.risk_level, C['green'])

        # Glow background for HIGH risk
        if self.risk_level == 'HIGH':
            glow_alpha = 0.10 + 0.08 * abs(math.sin(self._pulse_phase * 4))
            _alpha_rect(canvas, x+1, y+1, w-2, h-2, (30,10,60), glow_alpha)

        # Big label
        lbl = self.risk_level
        (lw, lh), _ = cv2.getTextSize(lbl, FONT_M, 0.70, 2)
        cx = x + w//2 - lw//2
        _put(canvas, lbl, (cx, y+52), scale=0.70, color=risk_col, thick=2, font=FONT_M)

        # Bar
        bx, by_, bw, bh = x+10, y+60, w-20, 8
        _rect(canvas, bx, by_, bw, bh, C['border'], 1)
        fill = int(bw * RISK_FILL.get(self.risk_level, 0.15))
        if fill > 0:
            # Animated fill for HIGH
            if self.risk_level == 'HIGH':
                fill = int(fill * (0.85 + 0.15 * abs(math.sin(self._pulse_phase * 5))))
            _rect(canvas, bx, by_, fill, bh, risk_col, -1)

        # Tick labels
        for i, lbl_ in enumerate(['LOW','MED','HIGH']):
            tx = bx + i*(bw//2) - 5
            _put(canvas, lbl_, (tx, by_+20), scale=0.26, color=C['text_dim'])

        # Confidence percentage
        pct = int(RISK_FILL.get(self.risk_level, 0.15) * 100)
        _put(canvas, f"{pct}%", (x+w-28, y+52), scale=0.30, color=risk_col)

    # ── Detections Panel ──────────────────────────────────────
    def _draw_detections_panel(self, canvas, dets, x, y, w, h):
        _rect(canvas, x, y, w, h, C['panel_alt'], -1)
        _rect(canvas, x, y, w, h, C['border'], 1)

        count = len(dets)
        _put(canvas, f"DETECTIONS  [{count}]", (x+8, y+13), scale=0.30, color=C['text_dim'])
        _hline(canvas, y+17, x, x+w, C['border'])

        by = y + 30
        for det in dets[:7]:
            label   = det.get('label', 'OBJ').upper()
            conf    = det.get('conf',  0.0)
            tid     = det.get('track_id')
            dcol    = DET_COLORS.get(label.lower(), C['green'])

            # Label + track id
            id_str = f"#{tid}" if tid is not None else ""
            _put(canvas, label, (x+8, by), scale=0.34, color=dcol, thick=1)
            _put(canvas, id_str, (x+8, by+12), scale=0.26, color=C['text_dim'])

            # Conf bar
            bx2, bw2, bh2 = x+72, w-110, 4
            _rect(canvas, bx2, by-9, bw2, bh2, C['border'], 1)
            _rect(canvas, bx2, by-9, int(bw2*conf), bh2, dcol, -1)

            # Conf number
            _put(canvas, f"{conf:.2f}", (x+w-36, by), scale=0.30, color=C['text_dim'])
            by += 26

        if count == 0:
            _put(canvas, "No objects detected", (x+8, y+40), scale=0.32, color=C['text_dim'])

    # ── VLM Panel ─────────────────────────────────────────────
    def _draw_vlm_panel(self, canvas, x, y, w, h):
        _rect(canvas, x, y, w, h, C['panel'], -1)
        _rect(canvas, x, y, w, h, C['border'], 1)

        # Animated dot
        dot_alpha = 0.5 + 0.5 * abs(math.sin(self._pulse_phase * 2))
        dot_col = tuple(int(c * dot_alpha) for c in C['amber'])
        cv2.circle(canvas, (x+10, y+10), 4, dot_col, -1)

        _put(canvas, "VLM INFERENCE  ·  MOONDREAM2 / LLAVA", (x+18, y+14),
             scale=0.28, color=C['text_dim'])
        _hline(canvas, y+18, x, x+w, C['border'])

        lines = _wrap_text(self.vlm_text, w-20, 0.36)
        ty = y + 33
        for line in lines[:4]:
            _put(canvas, line, (x+8, ty), scale=0.36, color=C['text'])
            ty += 19

    # ── Query Input Panel ─────────────────────────────────────
    def _draw_query_panel(self, canvas, x, y, w, h):
        _rect(canvas, x, y, w, h, C['input_bg'], -1)
        _rect(canvas, x, y, w, h, C['border_bright'] if self._input_active else C['border'], 1)

        # Label
        lbl_col = C['green'] if self._input_active else C['text_dim']
        prefix = ">_" if self._input_active else "·_"
        _put(canvas, prefix, (x+6, y+14), scale=0.35, color=lbl_col, thick=1)

        # Input text with blinking cursor
        display = self._input_text
        if self._input_active:
            if time.time() - self._blink_t > 0.5:
                self._input_blink = not self._input_blink
                self._blink_t = time.time()
            if self._input_blink:
                display += "|"

        _put(canvas, display, (x+24, y+14), scale=0.36, color=C['text_bright'])

        # Hint
        if not self._input_active and not self._input_text:
            _put(canvas, "Press [T] to type query  |  [V] for voice  |  [ENTER] to send  |  [Q] quit",
                 (x+24, y+14), scale=0.30, color=C['text_dim'])

        # STT listening animation
        if self.stt_active:
            bars = 8
            for i in range(bars):
                bh_ = int(5 + 10 * abs(math.sin(self._pulse_phase * 3 + i * 0.4)))
                bx_ = x + w - 100 + i * 11
                _rect(canvas, bx_, y + h//2 - bh_//2, 7, bh_, C['red_bright'], -1)

    # ── Alerts Overlay ────────────────────────────────────────
    def _draw_alerts(self, canvas):
        now = time.time()
        active = [(m,e,c) for m,e,c in self._alerts if now < e]
        self._alerts = active
        ay = 55
        for msg, expire, col in active:
            remaining = expire - now
            alpha = min(1.0, remaining * 2)  # fade out last 0.5s
            bw_ = 400
            _alpha_rect(canvas, 5, ay, bw_, 28, (0,0,0), alpha * 0.6)
            _rect(canvas, 5, ay, bw_, 28, col, 1)
            _put(canvas, f"⚠  {msg}", (14, ay+17), scale=0.38,
                 color=tuple(int(c*alpha) for c in col), thick=1)
            ay += 34

    # ── Detection Boxes on frame ───────────────────────────────
    def _draw_detection_boxes(self, canvas, dets, vx, vy, vw, vh):
        for det in dets:
            bx_  = det.get('x', 0.0)
            by_  = det.get('y', 0.0)
            bw_  = det.get('w', 0.1)
            bh_  = det.get('h', 0.1)
            label = det.get('label', 'OBJ').upper()
            conf  = det.get('conf', 0.0)
            tid   = det.get('track_id')
            dcol  = DET_COLORS.get(label.lower(), C['green'])

            px = vx + int(bx_ * vw)
            py = vy + int(by_ * vh)
            pw = int(bw_ * vw)
            ph = int(bh_ * vh)

            # Box
            cv2.rectangle(canvas, (px,py), (px+pw,py+ph), dcol, 1)
            _corner_marks(canvas, px, py, pw, ph, dcol, size=10, thick=2)

            # Track trail
            if tid is not None:
                cx_, cy_ = px + pw//2, py + ph//2
                hist = self._track_history.setdefault(tid, [])
                hist.append((cx_, cy_))
                if len(hist) > 20:
                    hist.pop(0)
                for i in range(1, len(hist)):
                    alpha_t = i / len(hist)
                    col_t = tuple(int(c * alpha_t) for c in dcol)
                    cv2.line(canvas, hist[i-1], hist[i], col_t, 1, cv2.LINE_AA)

            # Label tag
            tag = f"{label}"
            if tid is not None:
                tag += f" #{tid}"
            (tw, th_), _ = cv2.getTextSize(tag, FONT, 0.30, 1)
            _rect(canvas, px, py-th_-6, tw+8, th_+6, dcol, -1)
            _put(canvas, tag, (px+4, py-4), scale=0.30, color=C['bg'])

            # Conf below box
            _put(canvas, f"{conf:.0%}", (px, py+ph+12), scale=0.28, color=dcol)

    # ── Crosshair ─────────────────────────────────────────────
    def _draw_crosshair(self, canvas, cx, cy, size=28):
        gap = 6
        col = C['green_dim']
        cv2.line(canvas, (cx-size,cy), (cx-gap,cy), col, 1, cv2.LINE_AA)
        cv2.line(canvas, (cx+gap,cy), (cx+size,cy), col, 1, cv2.LINE_AA)
        cv2.line(canvas, (cx,cy-size), (cx,cy-gap), col, 1, cv2.LINE_AA)
        cv2.line(canvas, (cx,cy+gap), (cx,cy+size), col, 1, cv2.LINE_AA)
        cv2.circle(canvas, (cx,cy), 3, col, 1, cv2.LINE_AA)
        cv2.circle(canvas, (cx,cy), 14, (*col[:3],), 1, cv2.LINE_AA)

    # ── Grid overlay ──────────────────────────────────────────
    def _draw_grid(self, canvas, x, y, w, h):
        step = 60
        for gx in range(x, x+w, step):
            _alpha_rect(canvas, gx, y, 1, h, (20,55,35), 0.4)
        for gy in range(y, y+h, step):
            _alpha_rect(canvas, x, gy, w, 1, (20,55,35), 0.4)

    # ── Bottom Status Bar ─────────────────────────────────────
    def _draw_status_bar(self, canvas, y, w):
        _alpha_rect(canvas, 0, y, w, self.H-y, (6,14,10), 0.93)
        _hline(canvas, y, 0, w, C['border_bright'], 1)
        _put(canvas,
             f"[T] TYPE QUERY   [V] VOICE INPUT   [C] CLEAR   [S] SNAPSHOT   [R] RESET   [Q] QUIT",
             (10, y+15), scale=0.29, color=C['text_dim'])
        _put(canvas,
             f"SYS {self._uptime()}  |  FPS {self.fps:.0f}  |  RISK {self.risk_level}  |  OBJS {len(self.detections)}",
             (10, y+30), scale=0.28, color=C['green_dim'])

    # ── Main Update ───────────────────────────────────────────
    def update(self, frame, detections, risk_level, vlm_response):
        now = time.time()
        dt  = now - self._last_render
        self._last_render = now

        # Update phases
        self._scan_phase  = (self._scan_phase + dt * 0.18) % 1.0
        self._pulse_phase = (self._pulse_phase + dt * 1.2) % (2 * math.pi)

        # FPS
        self._frame_times.append(now)
        self._frame_times = [t for t in self._frame_times if now - t < 1.0]
        self.fps = float(len(self._frame_times))

        self.risk_level = risk_level
        self.vlm_text   = vlm_response
        self.detections = detections

        W, H = self.W, self.H

        # ── Layout ────────────────────────────────────────────
        HDR   = 44
        BOT   = 38
        SIDE  = 210
        VLM_H = 85
        QRY_H = 36

        vx  = 0
        vy  = HDR
        vw  = W - SIDE
        vh  = H - HDR - BOT - VLM_H - QRY_H
        sx  = W - SIDE
        rph = 90
        dph = H - HDR - BOT - VLM_H - QRY_H - rph

        # ── Canvas ────────────────────────────────────────────
        canvas = np.zeros((H, W, 3), dtype=np.uint8)
        canvas[:] = C['bg']

        # ── Camera frame ──────────────────────────────────────
        if frame is not None:
            try:
                resized = cv2.resize(frame, (vw, vh), interpolation=cv2.INTER_LINEAR)
                # Slight contrast boost
                resized = cv2.convertScaleAbs(resized, alpha=1.05, beta=3)
                canvas[vy:vy+vh, vx:vx+vw] = resized
            except Exception:
                pass

        # Grid & scan
        self._draw_grid(canvas, vx, vy, vw, vh)
        self._draw_scan_bar(canvas, vx, vy, vw, vh)
        self._draw_scanlines(canvas, vx, vy, vw, vh)

        # Detection overlays
        norm_dets = self._normalise_detections(detections, vw, vh)
        self._draw_detection_boxes(canvas, norm_dets, vx, vy, vw, vh)
        self._draw_crosshair(canvas, vx+vw//2, vy+vh//2)

        # Border around viewport
        cv2.rectangle(canvas, (vx,vy), (vx+vw-1, vy+vh-1), C['border_bright'], 1)
        _corner_marks(canvas, vx, vy, vw-1, vh-1, C['green_dim'], size=16, thick=1)

        # ── Side panels ───────────────────────────────────────
        self._draw_side_bg(canvas, sx, HDR, SIDE, H - HDR - BOT)
        self._draw_risk_panel(canvas, sx, HDR, SIDE, rph)
        _hline(canvas, HDR+rph, sx, W, C['border'])
        self._draw_detections_panel(canvas, norm_dets, sx, HDR+rph, SIDE, dph)

        # ── VLM panel (below viewport) ────────────────────────
        vy_vlm = HDR + vh
        self._draw_vlm_panel(canvas, 0, vy_vlm, vw, VLM_H)

        # ── Query input panel ─────────────────────────────────
        vy_q = vy_vlm + VLM_H
        self._draw_query_panel(canvas, 0, vy_q, vw, QRY_H)

        # ── Header ────────────────────────────────────────────
        self._draw_header(canvas)

        # ── Alerts ────────────────────────────────────────────
        self._draw_alerts(canvas)

        # ── Bottom bar ────────────────────────────────────────
        self._draw_status_bar(canvas, H - BOT, W)

        cv2.imshow(self.window_name, canvas)
        return self._handle_keys()

    # ── Key handling ──────────────────────────────────────────
    def _handle_keys(self):
        key = cv2.waitKey(1) & 0xFF
        if key == 255:
            return None

        # Typing mode
        if self._input_active:
            if key == 13:   # ENTER — submit
                if self._input_text.strip():
                    self.user_query_queue.put(self._input_text.strip())
                    self._input_text = ""
                self._input_active = False
                return None
            elif key == 27: # ESC — cancel
                self._input_text  = ""
                self._input_active = False
                return None
            elif key == 8 or key == 127:  # BACKSPACE
                self._input_text = self._input_text[:-1]
            elif 32 <= key <= 126:
                self._input_text += chr(key)
            return None

        # Normal mode
        if key == ord('q') or key == ord('Q'):
            return 'quit'
        elif key == ord('t') or key == ord('T'):
            self._input_active = True
            self._input_text   = ""
            return None
        elif key == ord('v') or key == ord('V'):
            return 'voice'
        elif key == ord('c') or key == ord('C'):
            self._input_text  = ""
            self._input_active = False
            return None
        elif key == ord('s') or key == ord('S'):
            return 'snapshot'
        elif key == ord('r') or key == ord('R'):
            return 'reset'
        return None

    # ── Normalise detections ──────────────────────────────────
    def _normalise_detections(self, detections, vw, vh):
        """Convert from VisionDetector format to UI format."""
        out = []
        for det in detections:
            bbox  = det.get('bbox', None)
            label = det.get('class_name', det.get('label', 'obj'))
            conf  = det.get('confidence', det.get('conf', 0.0))
            tid   = det.get('track_id')
            if bbox is not None and len(bbox) == 4:
                x1, y1, x2, y2 = bbox
                # bbox is in original frame coords (640x480 or similar)
                # We'll pass raw and let draw handle them directly
                out.append({
                    'label': label, 'conf': conf, 'track_id': tid,
                    'bbox_abs': (int(x1), int(y1), int(x2), int(y2)),
                    'x': 0, 'y': 0, 'w': 0, 'h': 0
                })
            else:
                out.append({'label': label, 'conf': conf, 'track_id': tid,
                            'x': det.get('x',0), 'y': det.get('y',0),
                            'w': det.get('w',0), 'h': det.get('h',0)})
        return out

    def _draw_detection_boxes(self, canvas, dets, vx, vy, vw, vh):
        # Override to support both abs bbox and normalised
        for det in dets:
            label = det.get('label', 'OBJ').upper()
            conf  = det.get('conf',  0.0)
            tid   = det.get('track_id')
            dcol  = DET_COLORS.get(label.lower(), C['green'])

            bbox_abs = det.get('bbox_abs')
            if bbox_abs:
                # Scale from original cam res to viewport
                orig_w, orig_h = 640, 480   # default cam res
                x1, y1, x2, y2 = bbox_abs
                scale_x = vw / orig_w
                scale_y = vh / orig_h
                px = vx + int(x1 * scale_x)
                py = vy + int(y1 * scale_y)
                pw = int((x2 - x1) * scale_x)
                ph = int((y2 - y1) * scale_y)
            else:
                px = vx + int(det['x'] * vw)
                py = vy + int(det['y'] * vh)
                pw = int(det['w'] * vw)
                ph = int(det['h'] * vh)

            pw = max(pw, 10); ph = max(ph, 10)
            cv2.rectangle(canvas, (px,py), (px+pw,py+ph), dcol, 1)
            _corner_marks(canvas, px, py, pw, ph, dcol, size=10, thick=2)

            # Trail
            if tid is not None:
                cx_, cy_ = px + pw//2, py + ph//2
                hist = self._track_history.setdefault(tid, [])
                hist.append((cx_, cy_))
                if len(hist) > 25:
                    hist.pop(0)
                for i in range(1, len(hist)):
                    alpha_t = i / len(hist)
                    col_t = tuple(int(c * alpha_t) for c in dcol)
                    cv2.line(canvas, hist[i-1], hist[i], col_t, 1, cv2.LINE_AA)

            # Tag
            tag = f"{label}  #{tid}" if tid is not None else label
            (tw, th_), _ = cv2.getTextSize(tag, FONT, 0.30, 1)
            _rect(canvas, px, py-th_-5, tw+8, th_+5, dcol, -1)
            _put(canvas, tag, (px+4, py-3), scale=0.30, color=C['bg'])
            _put(canvas, f"{conf:.0%}", (px, py+ph+11), scale=0.26, color=dcol)

    def close(self):
        cv2.destroyAllWindows()

import sqlite3
import cv2
import os
from datetime import datetime
from config import DB_PATH, FRAMES_DIR

class DatabaseLogger:
    """SQLite logging with frame snapshots."""
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                risk_level TEXT,
                description TEXT,
                suggested_action TEXT,
                frame_path TEXT
            )
        ''')
        self.conn.commit()

    def log_event(self, risk_level, description, suggested_action, frame=None):
        timestamp = datetime.now().isoformat()
        frame_path = None
        if frame is not None and risk_level in ['HIGH', 'MEDIUM']:
            filename = f"{timestamp.replace(':', '-')}.jpg"
            frame_path = os.path.join(FRAMES_DIR, filename)
            cv2.imwrite(frame_path, frame)

        self.cursor.execute('''
            INSERT INTO events (timestamp, risk_level, description, suggested_action, frame_path)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, risk_level, description, suggested_action, frame_path))
        self.conn.commit()
        return frame_path

    def close(self):
        self.conn.close()
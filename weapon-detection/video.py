"""Threaded capture: always returns the newest frame -> low latency, no buffer lag."""
import cv2, threading, time

class ThreadedCapture:
    def __init__(self, source=0):
        self.source = int(source) if str(source).isdigit() else source
        self.is_file = isinstance(self.source, str) and not self.source.startswith("rtsp")
        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open video source: {source}")
        self.frame, self.ok, self.lock = None, True, threading.Lock()
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        delay = 1 / (self.cap.get(cv2.CAP_PROP_FPS) or 30) if self.is_file else 0
        while self.ok:
            ret, f = self.cap.read()
            if not ret:
                if self.is_file:                       # loop video files
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0); continue
                time.sleep(0.5); self.cap.open(self.source); continue
            with self.lock: self.frame = f
            if delay: time.sleep(delay)

    def read(self):
        with self.lock:
            return None if self.frame is None else self.frame.copy()

    def release(self):
        self.ok = False; time.sleep(0.1); self.cap.release()

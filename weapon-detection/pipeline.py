"""Real-time pipeline shared by the CLI window and the web dashboard."""
import cv2, time, threading, yaml
from detector import Detector
from engine import ThreatEngine
from alerts import AlertManager
from video import ThreadedCapture

COLORS = {"SAFE": (90, 200, 90), "LOW": (0, 210, 255), "HIGH": (0, 130, 255), "CRITICAL": (0, 0, 255)}

def load_config(path="config.yaml"):
    with open(path) as f: return yaml.safe_load(f)

class WeaponMonitor:
    def __init__(self, cfg):
        self.cfg = cfg
        self.det, self.engine = Detector(cfg), ThreatEngine(cfg)
        self.alerts, self.cap = AlertManager(cfg), ThreadedCapture(cfg["source"])
        self.lock, self.jpeg, self.running = threading.Lock(), None, False
        self.stats = {"fps": 0.0, "level": "SAFE", "weapons": 0, "persons": 0, "alerts": 0, "latency_ms": 0}
        self.frame = None

    def start(self):
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()
        return self

    def stop(self):
        self.running = False; self.cap.release()

    def set_conf(self, v): self.det.conf = float(v)

    def _draw(self, img, dets, level):
        h, w = img.shape[:2]
        z = self.cfg.get("zone")
        if z:
            cv2.rectangle(img, (int(z[0]*w), int(z[1]*h)), (int(z[2]*w), int(z[3]*h)), (255, 200, 0), 1)
        for d in dets:
            x1, y1, x2, y2 = d["box"]
            col = COLORS["CRITICAL"] if d["active"] else (200, 160, 60)
            cv2.rectangle(img, (x1, y1), (x2, y2), col, 3 if d["active"] else 1)
            if d["active"] or d["name"] == "person":
                txt = f"{d['name']} {d['conf']:.0%}"
                cv2.rectangle(img, (x1, y1 - 20), (x1 + 9 * len(txt), y1), col, -1)
                cv2.putText(img, txt, (x1 + 3, y1 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        col = COLORS[level]
        cv2.rectangle(img, (0, 0), (w, 34), (20, 20, 20), -1)
        cv2.putText(img, f"THREAT: {level}   FPS: {self.stats['fps']:.1f}", (10, 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, col, 2)
        if level in ("HIGH", "CRITICAL"):
            cv2.rectangle(img, (0, 0), (w - 1, h - 1), col, 6)
        return img

    def _loop(self):
        fps = 0.0
        while self.running:
            frame = self.cap.read()
            if frame is None: time.sleep(0.01); continue
            t0 = time.time()
            dets = self.det.infer(frame)
            level = self.engine.update(dets, frame.shape)
            dt = time.time() - t0
            fps = 0.9 * fps + 0.1 / max(dt, 1e-6) if fps else 1 / max(dt, 1e-6)
            self.stats.update(fps=fps, level=level, latency_ms=int(dt * 1000),
                              weapons=sum(d["active"] for d in dets),
                              persons=sum(d["name"] == "person" for d in dets))
            out = self._draw(frame, dets, level)
            if level in ("HIGH", "CRITICAL"):
                self.alerts.trigger(level, out, [d for d in dets if d["active"]])
            self.stats["alerts"] = self.alerts.count
            self.frame = out
            ok, buf = cv2.imencode(".jpg", out, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ok:
                with self.lock: self.jpeg = buf.tobytes()

    def mjpeg(self):
        while True:
            with self.lock: j = self.jpeg
            if j: yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + j + b"\r\n"
            time.sleep(0.03)

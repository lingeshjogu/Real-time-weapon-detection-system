"""YOLOv8 wrapper -> list of dicts {name, conf, box, weapon}."""
from ultralytics import YOLO

class Detector:
    def __init__(self, cfg):
        m = cfg["model"]
        self.model = YOLO(m["weights"])
        self.conf, self.imgsz = m["conf"], m["imgsz"]
        self.device = None if m["device"] == "auto" else m["device"]
        self.names = self.model.names
        self.weapon_names = {n.lower() for n in cfg["weapon_classes"]}

    def infer(self, frame):
        r = self.model.predict(frame, conf=self.conf, imgsz=self.imgsz,
                               device=self.device, verbose=False)[0]
        out = []
        for b in r.boxes:
            name = self.names[int(b.cls)].lower()
            x1, y1, x2, y2 = map(int, b.xyxy[0].tolist())
            out.append({"name": name, "conf": float(b.conf), "box": (x1, y1, x2, y2),
                        "weapon": name in self.weapon_names, "active": False})
        return out

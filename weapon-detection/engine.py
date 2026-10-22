"""Threat engine: temporal confirmation + restricted zone + person association.
Levels: SAFE -> LOW (seen once) -> HIGH (confirmed) -> CRITICAL (confirmed AND held near a person)."""
from collections import deque

class ThreatEngine:
    def __init__(self, cfg):
        c = cfg["confirm"]
        self.need, self.hist = c["frames_required"], deque(maxlen=c["window"])
        self.zone = cfg.get("zone")

    def _in_zone(self, box, w, h):
        if not self.zone: return True
        cx, cy = (box[0] + box[2]) / 2 / w, (box[1] + box[3]) / 2 / h
        z = self.zone
        return z[0] <= cx <= z[2] and z[1] <= cy <= z[3]

    @staticmethod
    def _near(wb, pb):
        cx, cy = (wb[0] + wb[2]) / 2, (wb[1] + wb[3]) / 2
        pw, ph = pb[2] - pb[0], pb[3] - pb[1]
        return pb[0] - .1 * pw <= cx <= pb[2] + .1 * pw and pb[1] - .1 * ph <= cy <= pb[3] + .1 * ph

    def update(self, dets, shape):
        h, w = shape[:2]
        weapons = [d for d in dets if d["weapon"] and self._in_zone(d["box"], w, h)]
        for d in weapons: d["active"] = True
        persons = [d for d in dets if d["name"] == "person"]
        self.hist.append(bool(weapons))
        confirmed = sum(self.hist) >= self.need
        if confirmed:
            held = any(self._near(wp["box"], p["box"]) for wp in weapons for p in persons)
            return "CRITICAL" if held else "HIGH"
        return "LOW" if weapons else "SAFE"

"""Alerts: evidence snapshot + SQLite log + sound + optional Telegram, with cooldown."""
import cv2, os, time, sqlite3, threading, sys
from datetime import datetime

EVIDENCE = "evidence"

class AlertManager:
    def __init__(self, cfg):
        self.cfg = cfg["alerts"]; self.last = 0; self.count = 0
        os.makedirs(EVIDENCE, exist_ok=True)
        self.db = sqlite3.connect("events.db", check_same_thread=False)
        self.db.execute("""CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT, level TEXT, label TEXT, conf REAL, image TEXT)""")
        self.db.commit(); self.lock = threading.Lock()

    def trigger(self, level, frame, weapons):
        now = time.time()
        if now - self.last < self.cfg["cooldown_sec"] or not weapons: return False
        self.last = now; self.count += 1
        best = max(weapons, key=lambda d: d["conf"])
        fn = f"{datetime.now():%Y%m%d_%H%M%S}_{best['name'].replace(' ', '_')}.jpg"
        cv2.imwrite(os.path.join(EVIDENCE, fn), frame)
        with self.lock:
            self.db.execute("INSERT INTO events(ts,level,label,conf,image) VALUES(?,?,?,?,?)",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), level, best["name"], best["conf"], fn))
            self.db.commit()
        if self.cfg["sound"]: threading.Thread(target=self._beep, daemon=True).start()
        t = self.cfg["telegram"]
        if t["enabled"]:
            threading.Thread(target=self._telegram, args=(t, level, best, fn), daemon=True).start()
        print(f"[ALERT] {level}: {best['name']} ({best['conf']:.2f}) -> {fn}")
        return True

    def events(self, limit=15):
        with self.lock:
            rows = self.db.execute("SELECT ts,level,label,conf,image FROM events ORDER BY id DESC LIMIT ?",
                                   (limit,)).fetchall()
        return [dict(ts=r[0], level=r[1], label=r[2], conf=round(r[3], 2), image=r[4]) for r in rows]

    @staticmethod
    def _beep():
        try:
            if sys.platform.startswith("win"):
                import winsound
                for _ in range(3): winsound.Beep(1800, 300)
            else:
                print("\a\a\a", end="", flush=True)
        except Exception: pass

    @staticmethod
    def _telegram(t, level, d, fn):
        try:
            import requests
            with open(os.path.join(EVIDENCE, fn), "rb") as f:
                requests.post(f"https://api.telegram.org/bot{t['token']}/sendPhoto",
                    data={"chat_id": t["chat_id"], "caption": f"WEAPON ALERT [{level}]: {d['name']} {d['conf']:.0%}"},
                    files={"photo": f}, timeout=10)
        except Exception as e: print("Telegram failed:", e)

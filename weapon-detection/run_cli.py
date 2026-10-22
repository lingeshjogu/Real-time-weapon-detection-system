"""Desktop real-time window:  python run_cli.py --source 0"""
import argparse, cv2, time
from pipeline import WeaponMonitor, load_config

ap = argparse.ArgumentParser()
ap.add_argument("--source"); ap.add_argument("--weights"); ap.add_argument("--conf", type=float)
a = ap.parse_args()
cfg = load_config()
if a.source is not None: cfg["source"] = a.source
if a.weights: cfg["model"]["weights"] = a.weights
if a.conf: cfg["model"]["conf"] = a.conf

mon = WeaponMonitor(cfg).start()
print("Running... press 'q' to quit, 's' to save screenshot")
try:
    while True:
        f = mon.frame
        if f is not None:
            cv2.imshow("Real-Time Weapon Detection", f)
        k = cv2.waitKey(1) & 0xFF
        if k == ord("q"): break
        if k == ord("s") and f is not None: cv2.imwrite(f"shot_{int(time.time())}.jpg", f)
finally:
    mon.stop(); cv2.destroyAllWindows()

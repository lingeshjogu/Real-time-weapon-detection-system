"""Web dashboard:  python app.py --source 0   ->  http://localhost:5000"""
import argparse
from flask import Flask, Response, jsonify, render_template, request, send_from_directory
from pipeline import WeaponMonitor, load_config

ap = argparse.ArgumentParser()
ap.add_argument("--source"); ap.add_argument("--weights"); ap.add_argument("--port", type=int, default=5000)
a = ap.parse_args()
cfg = load_config()
if a.source is not None: cfg["source"] = a.source
if a.weights: cfg["model"]["weights"] = a.weights

monitor = WeaponMonitor(cfg).start()
app = Flask(__name__)

@app.route("/")
def index(): return render_template("index.html", conf=monitor.det.conf)

@app.route("/video_feed")
def video_feed():
    return Response(monitor.mjpeg(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/api/status")
def status(): return jsonify(monitor.stats)

@app.route("/api/events")
def events(): return jsonify(monitor.alerts.events())

@app.route("/api/conf", methods=["POST"])
def conf():
    monitor.set_conf(request.json["conf"]); return jsonify(ok=True, conf=monitor.det.conf)

@app.route("/evidence/<path:f>")
def evidence(f): return send_from_directory("evidence", f)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=a.port, threaded=True)

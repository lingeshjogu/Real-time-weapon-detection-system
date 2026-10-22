# Real-Time Weapon Detection System (Deep Learning)

YOLOv8-based real-time detector for handheld weapons (guns, knives) from webcam / video / RTSP CCTV streams,
with a live web dashboard.

## Distinctive features
- **Temporal confirmation** – alert only if a weapon appears in K of the last N frames (kills flicker false alarms)
- **4-level threat engine** – SAFE → LOW → HIGH → **CRITICAL** (weapon held near a detected person)
- **Restricted zone** – only raise alerts for weapons inside a region you define (`zone` in config.yaml)
- **Evidence logging** – every alert saves an annotated snapshot + SQLite record (`events.db`, `evidence/`)
- **Live dashboard** – MJPEG stream, FPS/latency, alert history with thumbnails, live sensitivity slider
- **Low-latency threaded capture** – always processes the newest frame; loops video files; reconnects dropped streams
- **Alerts** – sound alarm + optional Telegram photo notification, with cooldown
- Works with webcam, video file, or IP/RTSP camera

## Setup
```bash
python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run
```bash
python app.py --source 0                  # dashboard -> http://localhost:5000
python run_cli.py --source test.mp4       # plain OpenCV window (q = quit)
```
The default `yolov8n.pt` (COCO) detects **knife / scissors / baseball bat** out of the box, so you can demo immediately.
COCO has no gun class, so for firearms you must train a custom model:

## Train a weapon model
1. Download a YOLO-format weapon dataset (e.g. search "weapon detection" / "gun detection" on Roboflow Universe or Kaggle).
2. Place it in `datasets/weapons/{images,labels}/{train,val}` and edit class names in `data.yaml`.
3. `python train.py --epochs 50` (GPU strongly recommended; free option: Google Colab).
4. Set `model.weights: models/best.pt` in `config.yaml` and run again.

## Project structure
```
app.py        Flask dashboard           pipeline.py  real-time loop + drawing
run_cli.py    desktop window            detector.py  YOLOv8 wrapper
train.py      training script           engine.py    threat levels / zone / confirmation
config.yaml   all settings              alerts.py    snapshots, DB, sound, Telegram
video.py      threaded capture          templates/   dashboard UI
```

## Tuning tips
- Too many false alarms → raise `conf` or `frames_required`. Missing weapons → lower `conf`, train longer, add more varied data.
- Slow on CPU → use `yolov8n`, set `imgsz: 416`.
- For project report: evaluate with mAP@0.5, precision, recall (printed after training) and show the confusion matrix in `runs/weapon/`.

## Disclaimer
Academic/decision-support project. Any real deployment needs human verification of alerts.

"""Train on a weapon dataset:  python train.py --epochs 50 --model yolov8n.pt"""
import argparse, shutil
from ultralytics import YOLO

ap = argparse.ArgumentParser()
ap.add_argument("--data", default="data.yaml"); ap.add_argument("--model", default="yolov8n.pt")
ap.add_argument("--epochs", type=int, default=50); ap.add_argument("--imgsz", type=int, default=640)
ap.add_argument("--batch", type=int, default=16)
a = ap.parse_args()

m = YOLO(a.model)
m.train(data=a.data, epochs=a.epochs, imgsz=a.imgsz, batch=a.batch, project="runs", name="weapon", patience=15)
print(m.val())
shutil.copy("runs/weapon/weights/best.pt", "models/best.pt")
print("Saved models/best.pt -> set model.weights in config.yaml")

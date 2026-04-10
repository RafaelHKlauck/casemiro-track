import shutil
from ultralytics import YOLO
import os

os.makedirs("models", exist_ok=True)

shutil.copy(
    "runs/detect/casemiro-train/weights/best.pt",
    "models/parte_001.pt"
)

model = YOLO("models/parte_001.pt")
model.track(
    source="Primeiro tempo leve.mp4",
    tracker="botsort.yaml",
    conf=0.3,
    iou=0.5,
    persist=True,
    save=True,
    show=True
)
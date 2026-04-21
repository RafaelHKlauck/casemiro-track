import shutil
from ultralytics import YOLO
import os

os.makedirs("models", exist_ok=True)

model = YOLO("models/data-arg/parte_010-015_20-epochs.pt")
for result in model.track(
    name="parte_010-015_20-epochs",
    source="videos_teste/video_30min.mp4",
    tracker="botsort.yaml",
    conf=0.3,
    iou=0.5,
    persist=True,
    imgsz=640,
    save=True,
    stream=True,
):
    pass
from ultralytics import YOLO

if __name__ == "__main__":
    model = YOLO("runs/detect/casemiro-train/weights/last.pt")

    results = model.train(
        data="data.yaml",
        epochs=10,
        imgsz=640,
        batch=16,
        name="casemiro-train",
        exist_ok=True
    )
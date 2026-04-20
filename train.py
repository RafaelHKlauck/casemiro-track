from ultralytics import YOLO

if __name__ == "__main__":
    model = YOLO("runs/detect/casemiro-train/weights/last.pt")

    results = model.train(
        data="data.yaml",
        epochs=20,
        imgsz=640,
        batch=16,
        name="casemiro-train",
        exist_ok=True,

        # 🔄 Augmentations recomendadas
        fliplr=0.5,     # flip horizontal (importante)
        flipud=0.0,     # NÃO usar vertical

        scale=0.5,      # zoom (muito importante)
        translate=0.1,  # leve movimento da imagem

        hsv_h=0.015,    # cor (leve)
        hsv_s=0.7,      # saturação
        hsv_v=0.4,      # brilho (importante)

        mosaic=1.0,     # forte generalização
        mixup=0.15,     # leve mistura de imagens

        degrees=0.0,    # sem rotação (ou bem baixo)
    )
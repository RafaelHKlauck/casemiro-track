import argparse

from ultralytics import YOLO

from prepare_dataset import prepare_dataset_from_map

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Treino YOLO (Ultralytics)")
    parser.add_argument(
        "num_partes",
        type=int,
        nargs="?",
        default=None,
        metavar="N",
        help="Antes de treinar, monta dataset/ com as N primeiras partes do mapa (ex: 3 → parte_000 … parte_002).",
    )
    parser.add_argument(
        "--from",
        type=int,
        dest="from_n",
        metavar="N",
        default=None,
        help="Com --to: monta dataset só com parte_NNN no intervalo (ex: 10).",
    )
    parser.add_argument(
        "--to",
        type=int,
        dest="to_n",
        metavar="N",
        default=None,
        help="Com --from: inclusivo (ex: 15 → até parte_015).",
    )
    parser.add_argument(
        "--prepare-clean",
        action="store_true",
        help="Ao preparar dataset, apaga dataset/ inteira antes.",
    )
    args = parser.parse_args()

    prepare_run = (
        args.num_partes is not None
        or args.from_n is not None
        or args.to_n is not None
    )

    if prepare_run:
        if args.num_partes is not None and (
            args.from_n is not None or args.to_n is not None
        ):
            raise SystemExit(" Use só N na posição ou só --from/--to, não os dois.")

        if args.from_n is not None or args.to_n is not None:
            prepare_dataset_from_map(
                parte_from=args.from_n,
                parte_to=args.to_n,
                clean=args.prepare_clean,
            )
        else:
            prepare_dataset_from_map(num_partes=args.num_partes, clean=args.prepare_clean)

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

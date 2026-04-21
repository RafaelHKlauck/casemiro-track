#!/usr/bin/env python3
"""
Monta a pasta `dataset/` (YOLO) a partir do mapa unificado (symlinks).

Modos:
  - Primeiras N partes (ordenadas por número): prepare_dataset.py 3
  - Intervalo parte_NNN: prepare_dataset.py --from 10 --to 15

Requisitos: dataset_unificado/map.json (via build_map.py).

Train/val: seed 42, 30% val após shuffle (como organize.py).
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAP_PATH = os.path.join(BASE_DIR, "dataset_unificado", "map.json")
DATASET_DIR = os.path.join(BASE_DIR, "dataset")

SEED = 42
VAL_RATIO = 0.3


def parte_sort_key(name: str) -> int:
    m = re.search(r"parte_(\d+)", name)
    return int(m.group(1)) if m else -1


def symlink_force(src: str, dst: str) -> None:
    if os.path.lexists(dst):
        os.unlink(dst)
    os.symlink(src, dst)


def clear_leaf_dir(path: str) -> None:
    if not os.path.isdir(path):
        return
    for name in os.listdir(path):
        p = os.path.join(path, name)
        if os.path.isfile(p) or os.path.islink(p):
            os.unlink(p)


def prepare_dataset_from_map(
    *,
    num_partes: int | None = None,
    parte_from: int | None = None,
    parte_to: int | None = None,
    clean: bool = False,
) -> None:
    """
    Monta dataset/images e dataset/labels com symlinks.

    Use exatamente um modo:
    - num_partes: primeiras N entradas do mapa (parte_000, parte_001, …).
    - parte_from / parte_to: todas as pastas cujo número em parte_NNN está no intervalo inclusivo.
    """
    range_mode = parte_from is not None or parte_to is not None
    count_mode = num_partes is not None

    if range_mode and count_mode:
        raise ValueError("Use só um modo: --from/--to ou num_partes, não os dois.")

    if not range_mode and not count_mode:
        raise ValueError("Informe num_partes ou --from e --to.")

    if range_mode:
        if parte_from is None or parte_to is None:
            raise ValueError("Modo intervalo: informe --from e --to.")
        if parte_from > parte_to:
            raise ValueError("--from não pode ser maior que --to.")

    if count_mode and num_partes is not None and num_partes < 1:
        raise ValueError("num_partes deve ser >= 1")

    if not os.path.isfile(MAP_PATH):
        raise FileNotFoundError(
            f"Mapa não encontrado: {MAP_PATH}. Rode build_map.py primeiro."
        )

    with open(MAP_PATH, encoding="utf-8") as f:
        data = json.load(f)

    parts: list[dict] = sorted(data.get("parts", []), key=lambda e: parte_sort_key(e["folder"]))

    if not parts:
        raise ValueError("Mapa não tem nenhuma parte em 'parts'.")

    if count_mode:
        assert num_partes is not None
        if len(parts) < num_partes:
            raise ValueError(
                f"Mapa tem só {len(parts)} parte(s); pediu {num_partes}. "
                "Adicione mais pastas com build_map.py."
            )
        selected = parts[:num_partes]
    else:
        assert parte_from is not None and parte_to is not None
        selected = [
            p
            for p in parts
            if parte_from <= parte_sort_key(p["folder"]) <= parte_to
        ]
        if not selected:
            raise ValueError(
                f"Nenhuma parte no mapa entre parte_{parte_from:03d} e parte_{parte_to:03d} "
                "(pastas precisam do padrão nome parte_NNN)."
            )

    items: list[tuple[str, str]] = []
    global_idx = 0
    for entry in selected:
        for rel in entry["files"]:
            abs_src = os.path.join(BASE_DIR, rel)
            if not os.path.isfile(abs_src):
                raise FileNotFoundError(f"Arquivo listado no mapa não existe: {abs_src}")
            new_name = f"frame_{global_idx:06d}"
            items.append((abs_src, new_name))
            global_idx += 1

    random.seed(SEED)
    random.shuffle(items)

    split_index = int(len(items) * VAL_RATIO)
    val_items = items[:split_index]
    train_items = items[split_index:]

    images_train = os.path.join(DATASET_DIR, "images", "train")
    labels_train = os.path.join(DATASET_DIR, "labels", "train")
    images_val = os.path.join(DATASET_DIR, "images", "val")
    labels_val = os.path.join(DATASET_DIR, "labels", "val")

    if clean and os.path.isdir(DATASET_DIR):
        shutil.rmtree(DATASET_DIR)

    for d in (images_train, labels_train, images_val, labels_val):
        os.makedirs(d, exist_ok=True)

    for d in (images_train, labels_train, images_val, labels_val):
        clear_leaf_dir(d)

    missing = 0

    def link_batch(batch: list[tuple[str, str]], img_dest: str, lbl_dest: str) -> None:
        nonlocal missing
        for abs_img, stem in batch:
            dst_img = os.path.join(img_dest, stem + os.path.splitext(abs_img)[1])
            symlink_force(abs_img, dst_img)
            src_label = os.path.splitext(abs_img)[0] + ".txt"
            dst_lbl = os.path.join(lbl_dest, stem + ".txt")
            if os.path.isfile(src_label):
                symlink_force(src_label, dst_lbl)
            else:
                missing += 1

    print(f"Partes incluídas: {[e['folder'] for e in selected]}")
    print(f"Total de imagens: {len(items)} | train: {len(train_items)} | val: {len(val_items)} (seed={SEED})")

    link_batch(train_items, images_train, labels_train)
    link_batch(val_items, images_val, labels_val)

    if missing:
        print(f"⚠️  {missing} imagens sem label .txt correspondente")

    print(f"✅ dataset montado em {DATASET_DIR} (symlinks)")


def main() -> None:
    p = argparse.ArgumentParser(
        description="Cria dataset/ com symlinks a partir do mapa unificado."
    )
    p.add_argument(
        "num_partes",
        type=int,
        nargs="?",
        default=None,
        help="Primeiras N partes do mapa ordenadas (ex: 3 → parte_000 … parte_002)",
    )
    p.add_argument(
        "--from",
        type=int,
        dest="from_n",
        metavar="N",
        default=None,
        help="Modo intervalo: número inicial (ex: 10 → parte_010 em diante).",
    )
    p.add_argument(
        "--to",
        type=int,
        dest="to_n",
        metavar="N",
        default=None,
        help="Modo intervalo: número final inclusivo (ex: 15 → até parte_015).",
    )
    p.add_argument(
        "--clean",
        action="store_true",
        help="Remove a pasta dataset/ inteira antes de recriar",
    )
    args = p.parse_args()

    try:
        if args.num_partes is not None and (
            args.from_n is not None or args.to_n is not None
        ):
            raise ValueError("Não combine N na posição com --from/--to.")

        if args.from_n is not None or args.to_n is not None:
            prepare_dataset_from_map(
                parte_from=args.from_n,
                parte_to=args.to_n,
                clean=args.clean,
            )
        elif args.num_partes is not None:
            prepare_dataset_from_map(num_partes=args.num_partes, clean=args.clean)
        else:
            raise SystemExit(
                " Informe quantas partes (ex: prepare_dataset.py 3) ou --from N --to M"
            )
    except (ValueError, FileNotFoundError) as e:
        raise SystemExit(f" {e}") from e


if __name__ == "__main__":
    main()

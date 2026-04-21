#!/usr/bin/env python3
"""
Atualiza dataset_unificado/map.json com o intervalo global de índices de cada parte.

Uso:
  python build_map.py parte_007

Lê imagens em <pasta>/obj_train_data (igual ao organize.py). Todas as partes conhecidas
são ordenadas por número (parte_000, parte_001, …) e os índices globais 0…N-1 são
atribuídos nessa ordem. Pode rodar pasta a pasta: nada é apagado; cada execução
substitui só a entrada da pasta informada (se já existia) e recalcula os intervalos.

Para começar do zero, apague dataset_unificado/map.json.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UNIFIED_DIR = os.path.join(BASE_DIR, "dataset_unificado")
MAP_PATH = os.path.join(UNIFIED_DIR, "map.json")
OBJ_SUBDIR = "obj_train_data"
IMG_EXTENSIONS = (".png", ".jpg", ".jpeg")


def list_images(directory: str) -> list[str]:
    return sorted(
        f
        for f in os.listdir(directory)
        if f.lower().endswith(IMG_EXTENSIONS)
    )


def parte_sort_key(name: str) -> int:
    m = re.search(r"parte_(\d+)", name)
    return int(m.group(1)) if m else -1


def load_map() -> dict:
    if not os.path.isfile(MAP_PATH):
        return {"version": 1, "parts": []}
    with open(MAP_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_map(data: dict) -> None:
    os.makedirs(UNIFIED_DIR, exist_ok=True)
    with open(MAP_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def scan_folder(folder_name: str) -> tuple[str, list[str]]:
    obj_dir = os.path.join(BASE_DIR, folder_name, OBJ_SUBDIR)
    if not os.path.isdir(obj_dir):
        raise SystemExit(f" Pasta não encontrada ou sem {OBJ_SUBDIR}: {obj_dir}")
    images = list_images(obj_dir)
    if not images:
        raise SystemExit(f" Nenhuma imagem em {obj_dir}")
    rel_files = [f"{folder_name}/{OBJ_SUBDIR}/{name}" for name in images]
    return folder_name, rel_files


def recompute_indices(parts_entries: list[dict]) -> list[dict]:
    """Ordena por número da parte e atribui start/end sequenciais a partir de 0."""
    entries = sorted(parts_entries, key=lambda e: parte_sort_key(e["folder"]))
    out: list[dict] = []
    g = 0
    for e in entries:
        files = e["files"]
        n = len(files)
        start = g
        end = g + n - 1
        g += n
        out.append(
            {
                "folder": e["folder"],
                "start": start,
                "end": end,
                "count": n,
                "files": files,
            }
        )
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="Registra uma pasta parte_* no mapa unificado.")
    p.add_argument(
        "folder",
        help="Nome da pasta (ex: parte_012), na raiz do projeto",
    )
    args = p.parse_args()

    folder_name = os.path.basename(args.folder.strip().rstrip("/"))
    if not folder_name.startswith("parte_"):
        print("Aviso: o nome não começa com 'parte_'; continuando mesmo assim.", file=sys.stderr)

    _, new_files = scan_folder(folder_name)

    data = load_map()
    raw_parts: list[dict] = list(data.get("parts", []))

    merged: dict[str, list[str]] = {}
    for e in raw_parts:
        merged[e["folder"]] = list(e["files"])

    merged[folder_name] = new_files

    parts_entries = [{"folder": fn, "files": merged[fn]} for fn in merged]
    parts = recompute_indices(parts_entries)

    data["parts"] = parts
    data["next_index"] = parts[-1]["end"] + 1 if parts else 0

    save_map(data)

    slot = next(p for p in parts if p["folder"] == folder_name)
    print(f"Registrado {folder_name}: índices globais {slot['start']}–{slot['end']} ({slot['count']} imagens)")
    print(f"Mapa: {MAP_PATH} | total global: {data['next_index']} frames")


if __name__ == "__main__":
    main()

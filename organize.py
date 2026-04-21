import os
import re
import sys
import random
import shutil

SEED = 42
VAL_RATIO = 0.3
IMG_EXTENSIONS = (".png", ".jpg", ".jpeg")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEST_DIR = os.path.join(BASE_DIR, "dataset_last")

images_train_dir = os.path.join(DEST_DIR, "images", "train")
labels_train_dir = os.path.join(DEST_DIR, "labels", "train")
images_val_dir = os.path.join(DEST_DIR, "images", "val")
labels_val_dir = os.path.join(DEST_DIR, "labels", "val")

if len(sys.argv) < 2 or sys.argv[1] not in ("0", "1"):
    raise SystemExit("Uso: python organize.py <0|1>\n  0 = manter dataset_last anterior (acumular)\n  1 = deletar dataset_last antes de rodar")

CLEAN_MODE = sys.argv[1] == "1"


def parte_sort_key(name: str) -> int:
    """Extrai o número do nome da pasta (ex: 'parte_006' -> 6)."""
    match = re.search(r"parte_(\d+)", name)
    return int(match.group(1)) if match else -1


def list_images(directory: str) -> list[str]:
    return sorted(
        f for f in os.listdir(directory)
        if f.lower().endswith(IMG_EXTENSIONS)
    )


def copy_items(items: list[tuple[str, str]], source_dir: str, img_dest: str, label_dest: str):
    missing_labels = 0
    for original_name, new_name in items:
        ext = os.path.splitext(original_name)[1]
        label_name = os.path.splitext(original_name)[0] + ".txt"

        img_src = os.path.join(source_dir, original_name)
        label_src = os.path.join(source_dir, label_name)

        shutil.copy2(img_src, os.path.join(img_dest, new_name + ext))

        if os.path.exists(label_src):
            shutil.copy2(label_src, os.path.join(label_dest, new_name + ".txt"))
        else:
            missing_labels += 1

    if missing_labels:
        print(f"  ⚠️  {missing_labels} imagens sem label correspondente")


# --- limpa e recria dataset ---
if CLEAN_MODE and os.path.exists(DEST_DIR):
    shutil.rmtree(DEST_DIR)
    print("🗑️  dataset_last deletado (modo limpo)")

for d in (images_train_dir, labels_train_dir, images_val_dir, labels_val_dir):
    os.makedirs(d, exist_ok=True)

# --- descobre partes ordenadas por número ---
parte_folders = sorted(
    [f for f in os.listdir(BASE_DIR)
     if f.startswith("parte_") and os.path.isdir(os.path.join(BASE_DIR, f))],
    key=parte_sort_key,
)

if not parte_folders:
    raise SystemExit("Nenhuma pasta parte_* encontrada.")

last_parte = parte_folders[-1]
print(f"Partes encontradas: {parte_folders}")
print(f"Última parte (fonte): {last_parte}")

# --- calcula offset somando imagens de TODAS as partes anteriores ---
offset = 0
for folder in parte_folders[:-1]:
    obj_dir = os.path.join(BASE_DIR, folder, "obj_train_data")
    if not os.path.isdir(obj_dir):
        print(f"  {folder}: obj_train_data não encontrado, pulando")
        continue
    count = len(list_images(obj_dir))
    print(f"  {folder}: {count} imagens")
    offset += count

print(f"Offset total (partes anteriores): {offset}")

# --- lista imagens da última parte ---
last_dir = os.path.join(BASE_DIR, last_parte, "obj_train_data")
if not os.path.isdir(last_dir):
    raise SystemExit(f"obj_train_data não encontrado em {last_parte}")

images = list_images(last_dir)
print(f"  {last_parte}: {len(images)} imagens (serão copiadas)")

# --- renumeração contínua a partir do offset ---
items = [(img, f"frame_{offset + idx:06d}") for idx, img in enumerate(images)]

# --- split train/val ---
random.seed(SEED)
random.shuffle(items)

split_index = int(len(items) * VAL_RATIO)
val_items = items[:split_index]
train_items = items[split_index:]

print(f"\nSplit (seed={SEED}, val_ratio={VAL_RATIO}):")
print(f"  Train: {len(train_items)}")
print(f"  Val:   {len(val_items)}")
print(f"  Range: frame_{offset:06d} → frame_{offset + len(images) - 1:06d}")

# --- copia da última parte para dataset_last ---
print("\nCopiando train...")
copy_items(train_items, last_dir, images_train_dir, labels_train_dir)
print("Copiando val...")
copy_items(val_items, last_dir, images_val_dir, labels_val_dir)

print(f"\n✅ dataset_last criado com {len(images)} imagens de {last_parte} (offset={offset})")
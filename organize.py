import os
import random
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RAW_DATA_DIR = BASE_DIR
DEST_DIR = os.path.join(BASE_DIR, "dataset")

images_train_dir = os.path.join(DEST_DIR, "images", "train")
labels_train_dir = os.path.join(DEST_DIR, "labels", "train")

images_val_dir = os.path.join(DEST_DIR, "images", "val")
labels_val_dir = os.path.join(DEST_DIR, "labels", "val")

# limpa dataset (opcional, mas recomendado)
if os.path.exists(DEST_DIR):
    shutil.rmtree(DEST_DIR)

os.makedirs(images_train_dir)
os.makedirs(labels_train_dir)
os.makedirs(images_val_dir)
os.makedirs(labels_val_dir)

# -----------------------------
# pega parte_000, parte_001, ... ordenado
# -----------------------------
parte_folders = sorted([
    f for f in os.listdir(RAW_DATA_DIR)
    if f.startswith("parte_") and os.path.isdir(os.path.join(RAW_DATA_DIR, f))
])

print("Parte folders:", parte_folders)

# -----------------------------
# coleta tudo em ordem
# -----------------------------
all_items = []

for folder in parte_folders:
    source_dir = os.path.join(RAW_DATA_DIR, folder, "obj_train_data")

    if not os.path.exists(source_dir):
        continue

    images = sorted([
        f for f in os.listdir(source_dir)
        if f.endswith((".png", ".jpg"))
    ])

    for img in images:
        all_items.append((folder, img))

print("Total frames:", len(all_items))

# -----------------------------
# renumeração global
# -----------------------------
renamed_items = []

for idx, (folder, img) in enumerate(all_items):
    new_name = f"frame_{idx:06d}"
    renamed_items.append((folder, img, new_name))

# -----------------------------
# embaralha para split
# -----------------------------
random.shuffle(renamed_items)

split_index = int(len(renamed_items) * 0.3)
val_items = renamed_items[:split_index]
train_items = renamed_items[split_index:]

print(f"Train: {len(train_items)}")
print(f"Val: {len(val_items)}")

# -----------------------------
# copia com novo nome
# -----------------------------
def copy_items(items, img_dest, label_dest):
    for folder, img, new_name in items:
        source_dir = os.path.join(RAW_DATA_DIR, folder, "obj_train_data")

        label = img.replace(".png", ".txt").replace(".jpg", ".txt")

        img_src = os.path.join(source_dir, img)
        label_src = os.path.join(source_dir, label)

        img_dst = os.path.join(img_dest, new_name + ".png")
        label_dst = os.path.join(label_dest, new_name + ".txt")

        if os.path.exists(img_src):
            shutil.copy2(img_src, img_dst)

        if os.path.exists(label_src):
            shutil.copy2(label_src, label_dst)

copy_items(train_items, images_train_dir, labels_train_dir)
copy_items(val_items, images_val_dir, labels_val_dir)

print("✅ Dataset unificado e renumerado!")
from PIL import Image
import numpy as np
import os
from collections import deque

def load_and_mask(image_path):
    img = Image.open(image_path).convert("RGBA")
    np_img = np.array(img)

    if np_img.shape[2] == 4:
        mask = np_img[:, :, 3] > 0
    else:
        bg_color = tuple(np_img[0, 0])
        mask = np.any(np_img[:, :, :3] != bg_color, axis=2)

    return img, mask

def bfs(mask, visited, x, y):
    q = deque([(x, y)])
    coords = [(x, y)]
    visited[y, x] = True

    while q:
        cx, cy = q.popleft()
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = cx + dx, cy + dy
                if (
                    0 <= nx < mask.shape[1] and
                    0 <= ny < mask.shape[0] and
                    not visited[ny, nx] and
                    mask[ny, nx]
                ):
                    visited[ny, nx] = True
                    coords.append((nx, ny))
                    q.append((nx, ny))
    return coords

def extract_sprites(image_path):
    base_dir = os.path.dirname(image_path)
    output_dir = os.path.join(base_dir, "sprites")
    os.makedirs(output_dir, exist_ok=True)

    img, mask = load_and_mask(image_path)
    visited = np.zeros_like(mask, dtype=bool)
    seen_boxes = set()
    sprite_id = 0

    for y in range(mask.shape[0]):
        for x in range(mask.shape[1]):
            if mask[y, x] and not visited[y, x]:
                coords = bfs(mask, visited, x, y)
                xs = [pt[0] for pt in coords]
                ys = [pt[1] for pt in coords]
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)

                # Skip tiny noise regions
                if (max_x - min_x < 3) or (max_y - min_y < 3):
                    continue

                bbox = (min_x, min_y, max_x, max_y)
                if bbox in seen_boxes:
                    continue
                seen_boxes.add(bbox)

                sprite = img.crop((min_x, min_y, max_x + 1, max_y + 1))
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                sprite.save(os.path.join(output_dir, f"{base_name}_{sprite_id}.png"))
                sprite_id += 1

    print(f"{sprite_id} sprites extracted from {os.path.basename(image_path)}")

def main():
    path = input("Enter the path to a PNG file or folder: ").strip('"')

    if os.path.isfile(path) and path.lower().endswith(".png"):
        extract_sprites(path)
    elif os.path.isdir(path):
        for fname in os.listdir(path):
            if fname.lower().endswith(".png"):
                extract_sprites(os.path.join(path, fname))
    else:
        print("Invalid path. Please provide a PNG file or a folder containing PNGs.")

if __name__ == "__main__":
    main()

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

def extract_sprites(image_path, output_dir="sprites"):
    os.makedirs(output_dir, exist_ok=True)
    img, mask = load_and_mask(image_path)
    visited = np.zeros_like(mask, dtype=bool)
    sprite_id = 0

    for y in range(mask.shape[0]):
        for x in range(mask.shape[1]):
            if mask[y, x] and not visited[y, x]:
                coords = bfs(mask, visited, x, y)
                xs = [pt[0] for pt in coords]
                ys = [pt[1] for pt in coords]
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)

                sprite = img.crop((min_x, min_y, max_x + 1, max_y + 1))
                sprite.save(os.path.join(output_dir, f"sprite_{sprite_id}.png"))
                sprite_id += 1

    print(f"Extracted {sprite_id} sprites to '{output_dir}'")

extract_sprites("mario.png")
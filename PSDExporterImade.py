from psd_tools import PSDImage
from PIL import Image
import os

psd = PSDImage.open("cursedpharoah.psd")

output_dir = "exported_sprites"
os.makedirs(output_dir, exist_ok=True)

for i, layer in enumerate(psd.descendants()):
    if layer.is_group() or not layer.visible:
        continue

    image = layer.composite()
    if image:
        filename = f"{output_dir}/layer_{i}_{layer.name or 'unnamed'}.png"
        image.save(filename)
        print(f"Exported: {filename}")
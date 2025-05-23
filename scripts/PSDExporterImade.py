from psd_tools import PSDImage
from PIL import Image
import os

psd_path = input("Enter the full path to the PSD file: ").strip('"')
psd = PSDImage.open(psd_path)

base_dir = os.path.dirname(psd_path)
output_dir = os.path.join(base_dir, "exported_sprites")
os.makedirs(output_dir, exist_ok=True)

for i, layer in enumerate(psd.descendants()):
    if layer.is_group() or not layer.visible:
        continue

    image = layer.composite()
    if image:
        layer_name = layer.name or 'unnamed'
        filename = f"layer_{i}_{layer_name}.png"
        filepath = os.path.join(output_dir, filename)
        image.save(filepath)
        print(f"Exported: {filepath}")

import os
import re
import json
import shutil

# === Inputs ===
dom_document_path = input("Drag and drop your DOMDocument.xml here: ").strip().strip('"')
library_folder = input("Drag and drop your library folder here: ").strip().strip('"')
symbol_map_path = input("Drag and drop your symbol_map.json here: ").strip().strip('"')
data_json_path = input("Drag and drop your data.json here (or leave blank to skip): ").strip().strip('"')

# === Load rename map ===
with open(symbol_map_path, "r", encoding="utf-8") as f:
    rename_map = json.load(f)

print("Rename Map:")
for old, new in rename_map.items():
    print(f"  {old} > {new}")

# === 1. Update DOMDocument.xml ===
def update_domdocument(file_path, rename_map):
    if not os.path.exists(file_path):
        print("DOMDocument.xml not found.")
        return
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    for old, new in rename_map.items():
        content = re.sub(rf'\b{re.escape(old)}\b', new, content)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("DOMDocument.xml updated.")

# === 2. Rename PNGs in library/media/ ===
def rename_pngs(library_folder, rename_map):
    media_folder = os.path.join(library_folder, "media")
    if not os.path.exists(media_folder):
        print("media/ folder not found.")
        return
    for old, new in rename_map.items():
        old_png = os.path.join(media_folder, old + ".png")
        new_png = os.path.join(media_folder, new + ".png")
        if os.path.exists(old_png):
            shutil.move(old_png, new_png)
            print(f"Renamed PNG: {old}.png → {new}.png")
        else:
            print(f"PNG not found: {old}.png")

# === 3. Rename XMLs and update internals ===
def process_library_xmls(library_folder, rename_map):
    for root, dirs, files in os.walk(library_folder):
        for file in files:
            if not file.endswith(".xml"):
                continue
            path = os.path.join(root, file)
            name_only = file[:-4]

            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content

            for old, new in rename_map.items():
                # Update symbol definitions and references
                content = content.replace(f'name="image/{old}"', f'name="image/{new}"')
                content = content.replace(f'<DOMTimeline name="{old}">', f'<DOMTimeline name="{new}">')
                content = content.replace(f'libraryItemName="media/{old}"', f'libraryItemName="media/{new}"')
                content = content.replace(f'libraryItemName="image/{old}"', f'libraryItemName="image/{new}"')

            if content != original_content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Updated XML: {file}")

            # Rename XML file if needed
            if name_only in rename_map:
                new_name = rename_map[name_only] + ".xml"
                new_path = os.path.join(root, new_name)
                shutil.move(path, new_path)
                print(f"Renamed XML file: {file} → {new_name}")

# === 4. Update data.json image keys and IDs ===
def update_data_json(data_json_path, rename_map):
    if not data_json_path or not os.path.exists(data_json_path):
        print("data.json not found or skipped.")
        return

    with open(data_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "image" not in data:
        print("No 'image' block found in data.json.")
        return

    new_image_block = {}
    for key, value in data["image"].items():
        new_key = rename_map.get(key, key)

        # Automatically generate a cleaner ID based on the new name
        cleaned = new_key.upper().replace(" ", "_").replace("-", "_")
        cleaned = re.sub(r"[^A-Z0-9_]", "", cleaned)
        value["id"] = f"IMAGE_{cleaned}"

        new_image_block[new_key] = value

    data["image"] = new_image_block

    with open(data_json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print("data.json updated.")

# === Run Everything ===
update_domdocument(dom_document_path, rename_map)
rename_pngs(library_folder, rename_map)
process_library_xmls(library_folder, rename_map)
update_data_json(data_json_path, rename_map)

print("All done!")

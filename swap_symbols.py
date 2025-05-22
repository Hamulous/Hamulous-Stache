import os
import re
import json
import shutil

dom_document_path = input("Drag and drop your DOMDocument.xml here: ").strip().strip('"')
library_folder = input("Drag and drop your library folder here: ").strip().strip('"')
symbol_map_path = input("Drag and drop your symbol_map.json here: ").strip().strip('"')

# === Load the rename map ===
with open(symbol_map_path, "r", encoding="utf-8") as f:
    rename_map = json.load(f)

print("\n Rename Map:")
for old, new in rename_map.items():
    print(f"  {old} → {new}")

# === 1. Update the DOMDocument ===
def update_domdocument(file_path, rename_map):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    for old, new in rename_map.items():
        content = re.sub(rf'\b{re.escape(old)}\b', new, content)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(" DOMDocument.xml updated.")

# === 2. Rename the media folder's PNGs ===
def rename_pngs(library_folder, rename_map):
    media_folder = os.path.join(library_folder, "media")
    if not os.path.exists(media_folder):
        print(" media/ folder not found.")
        return
    for old, new in rename_map.items():
        old_png = os.path.join(media_folder, old + ".png")
        new_png = os.path.join(media_folder, new + ".png")
        if os.path.exists(old_png):
            shutil.move(old_png, new_png)
            print(f"Renamed PNG: {old}.png → {new}.png")
        else:
            print(f" PNG not found: {old}.png")

# === 3. Rename and update the XML's symbol files ===
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
            renamed = False

            for old, new in rename_map.items():
                # Replace DOMSymbolItem name, DOMTimeline name, libraryItemName
                content = content.replace(f'name="image/{old}"', f'name="image/{new}"')
                content = content.replace(f'<DOMTimeline name="{old}">', f'<DOMTimeline name="{new}">')
                content = content.replace(f'libraryItemName="media/{old}"', f'libraryItemName="media/{new}"')
                content = content.replace(f'libraryItemName="image/{old}"', f'libraryItemName="image/{new}"')

            if content != original_content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f" Updated XML: {file}")
                renamed = True

            # Fuck this took so much timeee
            if name_only in rename_map:
                new_name = rename_map[name_only] + ".xml"
                new_path = os.path.join(root, new_name)
                shutil.move(path, new_path)
                print(f" Renamed XML file: {file} → {new_name}")

# === Run all steps ===
update_domdocument(dom_document_path, rename_map)
rename_pngs(library_folder, rename_map)
process_library_xmls(library_folder, rename_map)

print("\n All updates completed successfully.")

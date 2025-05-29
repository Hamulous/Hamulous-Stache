import os
import re
import json
import shutil

# === SHARED ===
def prompt_input(prompt):
    return input(prompt).strip().strip('"').strip("'")

def update_domdocument(file_path, rename_map_or_func):
    if not os.path.exists(file_path):
        return
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    if callable(rename_map_or_func):
        content = rename_map_or_func(content)
    else:
        for old, new in rename_map_or_func.items():
            content = re.sub(rf'\b{re.escape(old)}\b', new, content)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated DOMDocument.xml")

def rename_pngs(library_folder, rename_map):
    media_folder = os.path.join(library_folder, "media")
    if not os.path.exists(media_folder):
        print("media/ folder not found.")
        return

    for file in os.listdir(media_folder):
        if not file.endswith(".png"):
            continue

        for old, new in rename_map.items():
            if file.startswith(old):
                old_path = os.path.join(media_folder, file)
                new_file = file.replace(old, new, 1)  # only replace the first match
                new_path = os.path.join(media_folder, new_file)
                shutil.move(old_path, new_path)
                print(f"Renamed PNG: {file} → {new_file}")
                break  # avoid double-matching


def rename_matching_pngs(media_folder, old, new):
    if not os.path.exists(media_folder):
        return
    for file in os.listdir(media_folder):
        if file.endswith(".png") and old in file:
            old_path = os.path.join(media_folder, file)
            new_file = file.replace(old, new)
            new_path = os.path.join(media_folder, new_file)
            shutil.move(old_path, new_path)
            print(f"Renamed PNG: {file} → {new_file}")

# === INTERACTIVE MODE ===
def run_interactive():
    dom_document_path = prompt_input("Drag and drop your DOMDocument.xml here: ")
    library_folder = prompt_input("Drag and drop your library folder here: ")
    data_json_path = prompt_input("Drag and drop your data.json here (or leave blank to skip): ")

    old_name = input("What name do you want to replace? ").strip()
    new_name = input("What should it be replaced with? ").strip()

    def rename_func(content):
        return content.replace(old_name, new_name)

    def update_library_xmls(library_folder, old, new):
        for root, _, files in os.walk(library_folder):
            for file in files:
                if not file.endswith(".xml"): continue
                path = os.path.join(root, file)
                name_only = file[:-4]
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                updated = content.replace(old, new)
                if updated != content:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(updated)
                    print(f"Updated XML: {file}")
                if old in name_only:
                    new_filename = file.replace(old, new)
                    new_path = os.path.join(root, new_filename)
                    shutil.move(path, new_path)
                    print(f"Renamed XML file: {file} → {new_filename}")

    def update_data_json(data_path, old, new):
        if not data_path or not os.path.exists(data_path): return
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "image" not in data: return
        new_image_block = {}
        for key, value in data["image"].items():
            new_key = key.replace(old, new)
            new_id = value["id"].replace(old.upper(), new.upper())
            value["id"] = new_id
            new_image_block[new_key] = value
        data["image"] = new_image_block
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print("Updated data.json")

    media_path = os.path.join(library_folder, "media")
    update_domdocument(dom_document_path, rename_func)
    rename_matching_pngs(media_path, old_name, new_name)
    update_library_xmls(library_folder, old_name, new_name)
    update_data_json(data_json_path, old_name, new_name)
    print("Interactive renaming complete!")

# === BULK MODE ===
def run_bulk():
    dom_document_path = prompt_input("Drag and drop your DOMDocument.xml here: ")
    library_folder = prompt_input("Drag and drop your library folder here: ")
    symbol_map_path = prompt_input("Drag and drop your symbol_map.json here (or leave blank to auto-generate): ")
    data_json_path = prompt_input("Drag and drop your data.json here (or leave blank to skip): ")

    rename_map = {}
    media_folder = os.path.join(library_folder, "media")

    if not symbol_map_path:
        print("No symbol_map.json provided. Auto-generating numbered rename map from media/...")
        if not os.path.exists(media_folder):
            print("media/ folder not found.")
            exit()
        files = sorted([f for f in os.listdir(media_folder) if f.endswith(".png")])
        for i, file in enumerate(files, start=1):
            name = file[:-4]
            rename_map[name] = f"RENAME_ME_{i}"
        base_folder = os.path.dirname(dom_document_path)
        auto_path = os.path.join(base_folder, "symbol_map.json")
        with open(auto_path, "w", encoding="utf-8") as f:
            json.dump(rename_map, f, indent=4)
        print(f"\nAuto-generated numbered symbol_map.json saved to: {auto_path}")
        print("Please open it and fill in the new names before running this script again.\n")
        return
    else:
        with open(symbol_map_path, "r", encoding="utf-8") as f:
            rename_map = json.load(f)

    def process_library_xmls(library_folder, rename_map):
        for root, _, files in os.walk(library_folder):
            for file in files:
                if not file.endswith(".xml"): continue
                path = os.path.join(root, file)
                name_only = file[:-4]
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                original = content
                for old, new in rename_map.items():
                    content = content.replace(old, new)
                if content != original:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"Updated XML: {file}")
                if name_only in rename_map and name_only != rename_map[name_only]:
                    new_name = rename_map[name_only] + ".xml"
                    new_path = os.path.join(root, new_name)
                    shutil.move(path, new_path)
                    print(f"Renamed XML file: {file} → {new_name}")

    def update_data_json(data_json_path, rename_map):
        if not data_json_path or not os.path.exists(data_json_path): return
        with open(data_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "image" not in data: return
        new_image_block = {}
        for key, value in data["image"].items():
            new_key = rename_map.get(key, key)
            cleaned = new_key.upper().replace(" ", "_").replace("-", "_")
            cleaned = re.sub(r"[^A-Z0-9_]", "", cleaned)
            value["id"] = f"IMAGE_{cleaned}"
            new_image_block[new_key] = value
        data["image"] = new_image_block
        with open(data_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print("data.json updated.")

    update_domdocument(dom_document_path, rename_map)
    rename_pngs(library_folder, rename_map)
    process_library_xmls(library_folder, rename_map)
    update_data_json(data_json_path, rename_map)
    print("Bulk renaming complete!")

# === MAIN SELECTOR ===
if __name__ == "__main__":
    print("Choose Symbol Renaming Mode:")
    print("[1] Bulk Symbol Swap (symbol_map.json)")
    print("[2] Interactive Rename (manual input)")
    choice = input("Enter 1 or 2: ").strip()
    if choice == "1":
        run_bulk()
    elif choice == "2":
        run_interactive()
    else:
        print("Invalid choice.")
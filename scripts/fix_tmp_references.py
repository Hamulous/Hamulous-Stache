import os
import shutil
import xml.etree.ElementTree as ET
import re
import json

def prompt_path(prompt_text):
    return input(f"{prompt_text}\n").strip().strip('"')

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def find_all_dombitmap_instances(elem):
    return elem.findall(".//{http://ns.adobe.com/xfl/2008/}DOMBitmapInstance")

def fix_xml(xml_path, media_path, backup_dir, renamed_map):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    namespace = {"xfl": "http://ns.adobe.com/xfl/2008/"}

    symbol_name = os.path.splitext(os.path.basename(xml_path))[0]
    modified = False

    for inst in find_all_dombitmap_instances(root):
        name_attr = inst.get("libraryItemName")
        if name_attr and "TMP" in name_attr:
            tmp_base = name_attr.split("/")[-1].replace(".png", "").replace(" copy", "")
            original_path = os.path.join(media_path, tmp_base + ".png")
            if not os.path.exists(original_path):
                continue

            new_filename = f"{symbol_name}.png"
            new_media_path = os.path.join(media_path, new_filename)

            if tmp_base not in renamed_map:
                renamed_map[tmp_base] = new_filename
                shutil.copy2(original_path, new_media_path)

            inst.set("libraryItemName", f"media/{symbol_name}")
            modified = True

    if modified:
        os.makedirs(os.path.join(backup_dir, "image_xmls"), exist_ok=True)
        shutil.copy2(xml_path, os.path.join(backup_dir, "image_xmls", os.path.basename(xml_path)))
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)
        print(f"[✓] Patched {os.path.basename(xml_path)} → media/{symbol_name}")
    return modified

def update_domdocument(dom_path, renamed_map, backup_dir):
    tree = ET.parse(dom_path)
    root = tree.getroot()
    namespace = {"xfl": "http://ns.adobe.com/xfl/2008/"}
    modified = False

    for item in root.findall(".//xfl:DOMBitmapItem", namespace):
        name_attr = item.get("name")
        if not name_attr or "TMP" not in name_attr:
            continue

        tmp_base = name_attr.split("/")[-1].replace(".png", "")
        if tmp_base in renamed_map:
            new_name = renamed_map[tmp_base].replace(".png", "")
            item.set("name", f"media/{new_name}")
            item.set("href", f"media/{new_name}")
            modified = True

    if modified:
        shutil.copy2(dom_path, dom_path + ".bak")
        tree.write(dom_path, encoding="utf-8", xml_declaration=True)
        print(f"    Updated DOMDocument.xml with renamed image references.")
    return modified

def update_data_json(xfl_root):
    data_json_path = os.path.join(xfl_root, "data.json")
    if not os.path.isfile(data_json_path):
        print(f"[!] No data.json found — skipping packet list update.")
        return

    packet_folder = os.path.join(xfl_root, "packet")
    if not os.path.isdir(packet_folder):
        return

    with open(data_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["packet"] = []

    for f in os.listdir(packet_folder):
        if f.lower().endswith(".scg"):
            data["packet"].append(f[:-4])

    with open(data_json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"[✓] Updated data.json with {len(data['packet'])} packets.")

def main():
    xfl_root = prompt_path("Drag and drop the .xfl folder here, then press Enter:")
    media_path = os.path.join(xfl_root, "library", "media")
    image_path = os.path.join(xfl_root, "library", "image")
    domdocument_path = os.path.join(xfl_root, "DOMDocument.xml")
    backup_dir = os.path.join(xfl_root, "xfl_tmpfix_backups")

    os.makedirs(backup_dir, exist_ok=True)
    renamed_map = {}
    patch_count = 0

    for file in os.listdir(image_path):
        if file.endswith(".xml"):
            full_path = os.path.join(image_path, file)
            if fix_xml(full_path, media_path, backup_dir, renamed_map):
                patch_count += 1

    dom_updated = update_domdocument(domdocument_path, renamed_map, backup_dir)
    update_data_json(xfl_root)

    print(f"\n Done. Patched {patch_count} image XML(s), copied TMPs, updated DOMDocument.xml.")
    print(f"   Backups saved to: {backup_dir}")
    print(f"   ├── media/        → original TMP PNGs")
    print(f"   └── image_xmls/   → original image XML files")
    print(f"   + DOMDocument.xml.bak at root\n")

if __name__ == "__main__":
    main()

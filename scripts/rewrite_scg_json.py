import os
import json

def gather_resource_entries(base_path):
    entries = {}

    # Scan resource/images/initial/
    initial_path = os.path.join(base_path, "resource", "images", "initial")
    if os.path.isdir(initial_path):
        for category in os.listdir(initial_path):
            category_path = os.path.join(initial_path, category)
            if not os.path.isdir(category_path):
                continue

            for name in os.listdir(category_path):
                item_path = os.path.join(category_path, name)
                if os.path.isdir(item_path):
                    popanim_key = f"POPANIM_{category.upper()}_{name.upper()}"
                    rel_path = os.path.relpath(item_path, base_path).replace("\\", "/")
                    entries[popanim_key] = {
                        "type": "PopAnim",
                        "path": rel_path
                    }

    # Scan resource/images/full/
    full_path = os.path.join(base_path, "resource", "images", "full")
    if os.path.isdir(full_path):
        for category in os.listdir(full_path):
            category_path = os.path.join(full_path, category)
            if not os.path.isdir(category_path):
                continue

            for name in os.listdir(category_path):
                item_path = os.path.join(category_path, name)
                if name.endswith(".pam.xfl") and os.path.isdir(item_path):
                    base_name = name.replace(".pam.xfl", "")
                    popanim_key = f"POPANIM_{category.upper()}_{base_name.upper()}"
                    rel_path = os.path.relpath(category_path, base_path).replace("\\", "/") + f"/{base_name}"
                    entries[popanim_key] = {
                        "type": "PopAnim",
                        "path": rel_path
                    }

    return entries

def main():
    package_path = input("Enter path to your .package folder (e.g. PlantPeashooter.package): ").strip('"')
    subgroup = input("Enter subgroup name (e.g. PlantPeashooter): ").strip()

    if not os.path.isdir(package_path):
        print("Invalid path. Please double-check the folder name.")
        return

    resource_entries = gather_resource_entries(package_path)

    data = {
        "#expand_method": "advanced",
        "version": 4,
        "texture_format_category": 0,
        "composite": True,
        "category": {
            "resolution": [1536, 768],
            "format": 147
        },
        "subgroup": {
            subgroup: {
                "category": {
                    "common_type": True,
                    "locale": None,
                    "compression": 3
                },
                "resource": resource_entries
            }
        }
    }

    output_path = os.path.join(package_path, "data.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print(f"data.json written to {output_path}")

if __name__ == "__main__":
    main()

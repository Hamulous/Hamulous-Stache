import json
import os

def convert_data_to_atlas(input_path, subgroup, base_path):
    input_path = input_path.strip('"')  # Clean drag-and-drop path

    # Load data.json
    with open(input_path, "r") as f:
        data = json.load(f)

    # Build atlas structure
    atlas = {
        "method": "path",
        "expand_path": "array",
        "subgroup": subgroup,
        "trim": False,
        "res": str(data["resolution"]),
        "groups": {}
    }

    # Populate groups using base path + image key
    for key, value in data["image"].items():
        atlas["groups"][value["id"]] = {
            "default": {
                "x": data["position"]["x"],
                "y": data["position"]["y"]
            },
            "path": f"{base_path.rstrip('/')}/{key}"
        }

    # Output to same folder as atlas.json
    output_path = input("Enter full path to the atlas.json you want to overwrite:\n").strip('"')
    with open(output_path, "w") as f:
        json.dump(atlas, f, indent=4)

    print(f"atlas.json successfully overwritten at:\n{output_path}")

if __name__ == "__main__":
    input_path = input("Drag your data.json here and press Enter:\n")
    subgroup = input("Enter the subgroup (e.g., PlantPeashooter): ").strip()
    base_path = input("Enter base path for each image (e.g., images/initial/plant/peashooter): ").strip()
    convert_data_to_atlas(input_path, subgroup, base_path)

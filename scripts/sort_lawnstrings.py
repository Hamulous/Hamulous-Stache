import json
import os

def sort_lawnstrings(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    
    for obj in data["objects"]:
        if obj["objclass"] == "LawnStringsData":
            loc_strings = obj["objdata"].get("LocStringValues", [])
            pairs = list(zip(loc_strings[::2], loc_strings[1::2]))
            pairs.sort()
            obj["objdata"]["LocStringValues"] = [item for pair in pairs for item in pair]
    
    dir_path = os.path.dirname(file_path)
    file_name = os.path.basename(file_path)
    output_path = os.path.join(dir_path, f"sorted_{file_name}")
    
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
    
    print(f"Sorted lawnstrings saved to: {output_path}")

if __name__ == "__main__":
    input_path = input("Enter the path to the LawnStrings JSON file: ").strip('"')
    sort_lawnstrings(input_path)

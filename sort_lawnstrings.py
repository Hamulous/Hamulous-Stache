import json

def sort_lawnstrings(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    
    for obj in data["objects"]:
        if obj["objclass"] == "LawnStringsData":
            loc_strings = obj["objdata"].get("LocStringValues", [])
            
            # We love sorting am I right guys?
            pairs = list(zip(loc_strings[::2], loc_strings[1::2]))
            pairs.sort()
            
            obj["objdata"]["LocStringValues"] = [item for pair in pairs for item in pair]
    
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


sort_lawnstrings("LAWNSTRINGS-EN-US.json")
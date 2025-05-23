import json
import os

def erase_levels(file_in, file_out):
    with open(file_in, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for obj in data.get("objects", []):
        for stat in obj.get("objdata", {}).get("FloatStats", []):
            if len(stat.get("Values", [])) > 1:
                stat["Values"] = stat["Values"][:1]
        
        if "StringStats" in obj.get("objdata", {}):
            for stat in obj["objdata"]["StringStats"]:
                if len(stat.get("Values", [])) > 1:
                    stat["Values"] = stat["Values"][:1]
        
        obj["objdata"]["LevelCap"] = 1
        obj["objdata"]["LevelCoins"] = []
        obj["objdata"]["LevelXP"] = []
        obj["objdata"]["UsesLeveling"] = False
        
        if "PlantTier" in obj["objdata"] and len(obj["objdata"]["PlantTier"]) > 1:
            obj["objdata"]["PlantTier"] = obj["objdata"]["PlantTier"][:1]
        
        print(f"Leveling removed for: {obj.get('aliases', ['Unknown'])[0]}")
    
    with open(file_out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def evaluate():
    file_in = input("Execution Argument: Input the path of your PLANTLEVELS.json to continue: ").strip('"')
    file_out = os.path.splitext(file_in)[0] + ".patch.json"
    erase_levels(file_in, file_out)

evaluate()

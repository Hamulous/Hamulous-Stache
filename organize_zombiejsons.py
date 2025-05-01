#Ty Stuff for the inspiration :salute: - Hamulous

import json

def get_name(s):
    """
        Extracts the name from a string formatted as "RTID(X@Y)".
    """
    return s.replace("RTID(", "").replace(")", "").replace("$", "").split("@")[0]

def main():
    
    with open("./packages/ZOMBIETYPES.json", "r", encoding="utf-8") as zombie_types:
        zombietypes_contents = json.load(zombie_types)
    with open("./packages/ZOMBIEPROPERTIES.json", "r", encoding="utf-8") as zombie_props:
        zombieprops_contents = json.load(zombie_props)
    with open("./packages/PROPERTYSHEETS.json", "r", encoding="utf-8") as property_sheets:
        propertysheets_contents = json.load(property_sheets)
    
    # property sheet crap
    for obj in propertysheets_contents["objects"]:
        if obj["objclass"] == "GamePropertySheet":
            zombie_list = obj["objdata"].get("ZombieAlmanacOrder", [])
            break
    
    # Fuck this took so much timeeee
    zombietypes_list = zombietypes_contents["objects"]
    new_zombietypes_list = []
    for zombiename in zombie_list:
        for zombietype in zombietypes_list:
            if "objdata" in zombietype and zombiename == zombietype["objdata"].get("TypeName", None):
                print(f"Adding {zombiename}")  # Debugging line
                new_zombietypes_list.append(zombietype)
                zombietypes_list.remove(zombietype)
                break

    for zombietype in zombietypes_list:
        if "objdata" in zombietype:  # Check for objdata existence
            print(f"Adding remaining {zombietype['objdata']['TypeName']}")  # Debugging line
            new_zombietypes_list.append(zombietype)
    
    # Tie it with zombie types to properties
    zombie_types_and_props = {}
    for zombietype in new_zombietypes_list:
        try:
            typename = zombietype["objdata"]["TypeName"]
            props = get_name(zombietype["objdata"]["Properties"])
            zombie_types_and_props[typename] = props
        except:
            continue
    
    # Now Organize
    zombieprops_list = zombieprops_contents["objects"]
    new_zombieprops_list = []
    for ztype in zombie_types_and_props:
        for zombieprop in zombieprops_list:
            try:
                # This just adjusts to handle the structure of zombie properties lololol
                if zombie_types_and_props[ztype] in zombieprop.get("aliases", []): 
                    new_zombieprops_list.append(zombieprop)
                    zombieprops_list.remove(zombieprop)
                    break
            except KeyError: 
                pass
    
    for zombieprop in zombieprops_list:
        new_zombieprops_list.append(zombieprop)

    with open("zombietypes_results.json", "w", encoding="utf-8") as file:
        zombietypes_contents["objects"] = new_zombietypes_list
        json.dump(zombietypes_contents, file, indent=4)
    with open("zombieprops_results.json", "w", encoding="utf-8") as file:
        zombieprops_contents["objects"] = new_zombieprops_list
        json.dump(zombieprops_contents, file, indent=4)
    
if __name__ == "__main__":
    main()
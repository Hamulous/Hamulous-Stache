import json
import os

def get_name(s):
    """
        Extracts the name from a string formatted as "RTID(X@Y)".
    """
    return s.replace("RTID(", "").replace(")", "").replace("$", "").split("@")[0]

def main():
    ztypes_path = input("Enter the path to ZOMBIETYPES.json: ").strip('"')
    zprops_path = input("Enter the path to ZOMBIEPROPERTIES.json: ").strip('"')
    psheets_path = input("Enter the path to PROPERTYSHEETS.json: ").strip('"')

    with open(ztypes_path, "r", encoding="utf-8") as zombie_types:
        zombietypes_contents = json.load(zombie_types)
    with open(zprops_path, "r", encoding="utf-8") as zombie_props:
        zombieprops_contents = json.load(zombie_props)
    with open(psheets_path, "r", encoding="utf-8") as property_sheets:
        propertysheets_contents = json.load(property_sheets)

    # Get zombie list from property sheet
    for obj in propertysheets_contents["objects"]:
        if obj["objclass"] == "GamePropertySheet":
            zombie_list = obj["objdata"].get("ZombieAlmanacOrder", [])
            break

    zombietypes_list = zombietypes_contents["objects"]
    new_zombietypes_list = []
    for zombiename in zombie_list:
        for zombietype in zombietypes_list:
            if "objdata" in zombietype and zombiename == zombietype["objdata"].get("TypeName", None):
                print(f"Adding {zombiename}")
                new_zombietypes_list.append(zombietype)
                zombietypes_list.remove(zombietype)
                break

    for zombietype in zombietypes_list:
        if "objdata" in zombietype:
            print(f"Adding remaining {zombietype['objdata']['TypeName']}")
            new_zombietypes_list.append(zombietype)

    zombie_types_and_props = {}
    for zombietype in new_zombietypes_list:
        try:
            typename = zombietype["objdata"]["TypeName"]
            props = get_name(zombietype["objdata"]["Properties"])
            zombie_types_and_props[typename] = props
        except:
            continue

    zombieprops_list = zombieprops_contents["objects"]
    new_zombieprops_list = []
    for ztype in zombie_types_and_props:
        for zombieprop in zombieprops_list:
            try:
                if zombie_types_and_props[ztype] in zombieprop.get("aliases", []):
                    new_zombieprops_list.append(zombieprop)
                    zombieprops_list.remove(zombieprop)
                    break
            except KeyError:
                pass

    for zombieprop in zombieprops_list:
        new_zombieprops_list.append(zombieprop)

    output_dir = os.path.dirname(ztypes_path)
    types_output_path = os.path.join(output_dir, "zombietypes_results.json")
    props_output_path = os.path.join(output_dir, "zombieprops_results.json")

    with open(types_output_path, "w", encoding="utf-8") as file:
        zombietypes_contents["objects"] = new_zombietypes_list
        json.dump(zombietypes_contents, file, indent=4)
    with open(props_output_path, "w", encoding="utf-8") as file:
        zombieprops_contents["objects"] = new_zombieprops_list
        json.dump(zombieprops_contents, file, indent=4)

    print(f"Saved organized zombietypes to: {types_output_path}")
    print(f"Saved organized zombieprops to: {props_output_path}")

if __name__ == "__main__":
    main()

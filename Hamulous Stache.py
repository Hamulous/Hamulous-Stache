import os
import json
from colorama import init, Fore, Style

init(autoreset=True)  # Enable colored output

def get_resource_path(relative_path):
    try:
        import sys
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_scripts(folder):
    folder_path = get_resource_path(folder)
    return [
        f for f in os.listdir(folder_path)
        if f.endswith(".py") and os.path.isfile(os.path.join(folder_path, f))
    ]

def load_name_map(path):
    try:
        with open(get_resource_path(path), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

# Define categories using arrays
CATEGORY_MAP = {
    "PvZ2 Tools": [
        "organize_zombiejsons.py",
        "organize_zombieactions.py",
        "sort_lawnstrings.py",
        "erase_plant_levels.py",
        "bulkadd_costumes.py",
        "dialogue.py",
        "swap_symbols.py"
    ],
    "Image/PSD Tools": [
        "ExportSprites.py",
        "PSDExporterImade.py",
        "Coolimageresizer.py"
    ]
}

def categorize_scripts(script_files):
    categories = {
        "PvZ2 Tools": [],
        "Image/PSD Tools": []
  
    }
    for file in script_files:
        found = False
        for category, file_list in CATEGORY_MAP.items():
            if file in file_list:
                categories[category].append(file)
                found = True
                break
        if not found:
            categories["Misc"].append(file)
    return categories

def main():
    SCRIPTS_FOLDER = "scripts"
    MAPPING_FILE = "script_names.json"

    folder_path = get_resource_path(SCRIPTS_FOLDER)
    if not os.path.isdir(folder_path):
        print(f"Folder '{folder_path}' not found.")
        return

    script_files = get_scripts(SCRIPTS_FOLDER)
    if not script_files:
        print("No Python scripts found in the folder.")
        return

    name_map = load_name_map(MAPPING_FILE)
    categorized = categorize_scripts(script_files)

    color_map = {
        "PvZ2 Tools": Fore.YELLOW,
        "Image/PSD Tools": Fore.MAGENTA    
    }

    while True:
        index_to_script = []
        print(Fore.CYAN + Style.BRIGHT + "\n=== Hamulous Stache Script Launcher ===")

        i = 1
        for category, scripts in categorized.items():
            if not scripts:
                continue
            print(color_map.get(category, "") + f"\n-- {category} --")
            for script_file in scripts:
                display_name = name_map.get(script_file, script_file)
                print(f"[{i}] {display_name}")
                index_to_script.append(script_file)
                i += 1

        try:
            choice = int(input("\nSelect a script to run: "))
            if 1 <= choice <= len(index_to_script):
                script_path = os.path.join(folder_path, index_to_script[choice - 1])
                with open(script_path, "r", encoding="utf-8") as f:
                    code = f.read()
                exec(code, {"__name__": "__main__"})
                print(Fore.CYAN + "\n--- Script finished ---\n")
            else:
                print(Fore.RED + "Invalid option.")
        except Exception as e:
            print(Fore.RED + f"Error: {e}")

if __name__ == "__main__":
    main()

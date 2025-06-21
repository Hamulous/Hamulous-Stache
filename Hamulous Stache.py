
import os
import json
import webbrowser
from colorama import init, Fore, Style

init(autoreset=True)

CONFIG_FILE = "hamulous_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"show_error_prompt": True, "has_seen_prompt": False}

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

def prompt_report_bug():
    print(Fore.YELLOW + "Would you like to report this issue?")
    print("[1] Yes, open the issue report page")
    print("[2] No")
    choice = input("> ").strip()

    if choice == "1":
        webbrowser.open("https://github.com/Hamulous/Hamulous-Stache/issues/new")

    # Ask whether to show this prompt again
    print(Fore.YELLOW + "Do you want to see this error prompt again in the future?")
    print("[1] No, don't show it again")
    print("[2] Yes, keep showing it")
    choice2 = input("> ").strip()
    config = load_config()
    if choice2 == "1":
        config["show_error_prompt"] = False
    else:
        config["show_error_prompt"] = True
    config["has_seen_prompt"] = True
    save_config(config)

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

CATEGORY_MAP = {
    "PvZ2 Tools": [
        "organize_zombiejsons.py",
        "organize_zombieactions.py",
        "sort_lawnstrings.py",
        "erase_plant_levels.py",
        "bulkadd_costumes.py",
        "dialogue.py",
        "swap_symbols.py",
        "data_to_atlas.py",
        "rewrite_scg_json.py",
        "speedup_labels.py", 
        "resize_label_matrices.py"
    ],
    "Image/PSD Tools": [
        "ExportSprites.py",
        "PSDExporterImade.py",
        "Coolimageresizer.py",
        "enhance_images.py"
    ]
}

def categorize_scripts(script_files):
    categories = {
        "PvZ2 Tools": [],
        "Image/PSD Tools": [],
        "Misc": []
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
        "Image/PSD Tools": Fore.MAGENTA,
        "Misc": Fore.GREEN
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
            print(Fore.RED + f"\n[!] Script crashed with error: {e}")
            config = load_config()
            if config.get("show_error_prompt", True) and not config.get("has_seen_prompt", False):
                prompt_report_bug()

if __name__ == "__main__":
    main()

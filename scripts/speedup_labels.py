import os
from xml.etree import ElementTree as ET

def find_label_xmls(folder):
    return [f for f in os.listdir(folder) if f.endswith(".xml")]

def speed_up_and_remove_frames(xml_path, speed_multiplier):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    ns = {'xfl': 'http://ns.adobe.com/xfl/2008/'}
    ET.register_namespace('', ns['xfl'])

    for layer in root.findall(".//xfl:DOMLayer", ns):
        frames = layer.findall("xfl:frames/xfl:DOMFrame", ns)
        new_frames = []
        for i, frame in enumerate(frames):
            if i == 0 or i % 2 == 1:
                duration = frame.get("duration")
                if duration and duration.isdigit():
                    new_duration = max(1, int(int(duration) / speed_multiplier))
                    frame.set("duration", str(new_duration))
                new_frames.append(frame)

        frames_container = layer.find("xfl:frames", ns)
        if frames_container is not None:
            for f in list(frames_container):
                frames_container.remove(f)
            frames_container.extend(new_frames)

    tree.write(xml_path, encoding="utf-8", xml_declaration=True)
    print(f"Sped up and removed even frames: {xml_path}")

def main():
    xfl_path = input("Drag your .xfl project folder here: ").strip('"')
    if not os.path.isdir(xfl_path):
        print("Invalid project folder.")
        return

    label_folder = os.path.join(xfl_path, "library", "label")
    if not os.path.isdir(label_folder):
        print("Could not find label folder at: library/label")
        return

    xml_files = find_label_xmls(label_folder)
    if not xml_files:
        print("No XML files found in label folder.")
        return

    print("\nAvailable label XMLs:")
    for i, fname in enumerate(xml_files, start=1):
        print(f"[{i}] {fname}")

    selected_files = []
    while True:
        choice = input("Enter label number to edit (or 0 to finish): ").strip()
        if choice == "0":
            break
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(xml_files):
                selected_files.append(xml_files[index])
            else:
                print("Invalid index.")
        else:
            print("Please enter a valid number.")

    if not selected_files:
        print("No valid files selected.")
        return

    speed_input = input("Speed multiplier (default is 2): ").strip()
    try:
        speed = float(speed_input) if speed_input else 2
        if speed <= 0:
            raise ValueError
    except ValueError:
        print("Invalid speed multiplier.")
        return

    for fname in selected_files:
        full_path = os.path.join(label_folder, fname)
        speed_up_and_remove_frames(full_path, speed)

if __name__ == "__main__":
    main()

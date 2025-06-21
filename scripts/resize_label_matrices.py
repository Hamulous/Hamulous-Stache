import os
import xml.etree.ElementTree as ET

def scale_matrix(matrix, scale):
    for attr in ["a", "b", "c", "d", "tx", "ty"]:
        if attr in matrix.attrib:
            original = float(matrix.attrib[attr])
            matrix.attrib[attr] = f"{original * scale:.6f}"

def resize_label_xml(xml_path, scale=1.0):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    ns = {"xfl": "http://ns.adobe.com/xfl/2008/"}
    ET.register_namespace('', ns["xfl"])

    for matrix in root.findall(".//xfl:Matrix", ns):
        scale_matrix(matrix, scale)

    tree.write(xml_path, encoding="utf-8", xml_declaration=True)
    print(f"Resized and saved: {xml_path}")

def find_label_xmls(folder):
    return [f for f in os.listdir(folder) if f.endswith(".xml")]

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

    print("\nResize Options:")
    print("[1] Resize all label XMLs")
    print("[2] Select label XMLs to resize one-by-one")
    option = input("Choose an option (1 or 2): ").strip()

    try:
        scale_input = input("Enter scale multiplier (e.g. 2 = 2x, 0.5 = shrink): ").strip()
        scale = float(scale_input)
        if scale <= 0:
            raise ValueError
    except ValueError:
        print("Invalid scale multiplier.")
        return

    if option == "1":
        for fname in xml_files:
            full_path = os.path.join(label_folder, fname)
            resize_label_xml(full_path, scale)

    elif option == "2":
        print("\nAvailable label XMLs:")
        for i, fname in enumerate(xml_files, start=1):
            print(f"[{i}] {fname}")

        selected_files = []
        while True:
            choice = input("Enter label number to resize (or 0 to finish): ").strip()
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

        for fname in selected_files:
            full_path = os.path.join(label_folder, fname)
            resize_label_xml(full_path, scale)

    else:
        print("Invalid option.")
        return

if __name__ == "__main__":
    main()

import os
import xml.etree.ElementTree as ET
import numpy as np

def scale_matrix(matrix, scale):
    for attr in ["a", "b", "c", "d", "tx", "ty"]:
        if attr in matrix.attrib:
            original = float(matrix.attrib[attr])
            matrix.attrib[attr] = f"{original * scale:.9f}"  # high precision

def extract_matrices(root, ns):
    matrices = []
    for matrix in root.findall(".//xfl:Matrix", ns):
        tx = float(matrix.attrib.get("tx", 0))
        ty = float(matrix.attrib.get("ty", 0))
        matrices.append((matrix, tx, ty))
    return matrices

def compute_average_center(matrices):
    if not matrices:
        return 0.0, 0.0
    tx_values = [tx for _, tx, _ in matrices]
    ty_values = [ty for _, _, ty in matrices]
    return np.mean(tx_values), np.mean(ty_values)

def shift_all_matrices(matrices, shift_x, shift_y):
    for matrix, _, _ in matrices:
        tx = float(matrix.attrib.get("tx", 0))
        ty = float(matrix.attrib.get("ty", 0))
        matrix.attrib["tx"] = f"{tx + shift_x:.9f}"
        matrix.attrib["ty"] = f"{ty + shift_y:.9f}"

def extract_symbol_bounds_from_domdoc(domdoc_path):
    bounds_dict = {}
    if not os.path.isfile(domdoc_path):
        return bounds_dict

    tree = ET.parse(domdoc_path)
    root = tree.getroot()
    for symbol in root.findall(".//DOMSymbolItem"):
        name = symbol.attrib.get("name")
        bounds = symbol.find("bounds")
        if name and bounds is not None:
            try:
                l = float(bounds.attrib.get("left", 0))
                t = float(bounds.attrib.get("top", 0))
                r = float(bounds.attrib.get("right", 0))
                b = float(bounds.attrib.get("bottom", 0))
                bounds_dict[name] = {
                    "center_x": (l + r) / 2,
                    "center_y": (t + b) / 2
                }
            except:
                continue
    return bounds_dict

def apply_symbol_bounds_offset(root, ns, symbol_bounds):
    for symbol_instance in root.findall(".//xfl:DOMSymbolInstance", ns):
        href = symbol_instance.attrib.get("libraryItemName")
        if href in symbol_bounds:
            center_x = symbol_bounds[href]["center_x"]
            center_y = symbol_bounds[href]["center_y"]
            for matrix in symbol_instance.findall(".//xfl:Matrix", ns):
                tx = float(matrix.attrib.get("tx", 0))
                ty = float(matrix.attrib.get("ty", 0))
                matrix.attrib["tx"] = f"{tx - center_x:.9f}"
                matrix.attrib["ty"] = f"{ty - center_y:.9f}"

def refine_resize_label_xml(xml_path, scale=1.0, symbol_bounds=None):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    ns = {"xfl": "http://ns.adobe.com/xfl/2008/"}
    ET.register_namespace('', ns["xfl"])

    original_matrices = extract_matrices(root, ns)
    original_center_x, original_center_y = compute_average_center(original_matrices)

    for matrix, _, _ in original_matrices:
        scale_matrix(matrix, scale)

    if symbol_bounds:
        apply_symbol_bounds_offset(root, ns, symbol_bounds)

    new_matrices = extract_matrices(root, ns)
    new_center_x, new_center_y = compute_average_center(new_matrices)

    shift_x = original_center_x - new_center_x
    shift_y = original_center_y - new_center_y
    shift_all_matrices(new_matrices, shift_x, shift_y)

    tree.write(xml_path, encoding="utf-8", xml_declaration=True)
    print(f"Refined and saved: {xml_path}")

def find_label_xmls(folder):
    return [f for f in os.listdir(folder) if f.endswith(".xml")]

def main():
    xfl_path = input("Drag your .xfl project folder here: ").strip('"')
    if not os.path.isdir(xfl_path):
        print("Invalid project folder.")
        return

    label_folder = os.path.join(xfl_path, "library", "label")
    domdoc_path = os.path.join(xfl_path, "DOMDocument.xml")

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

    selected_files = []
    if option == "1":
        selected_files = xml_files
    elif option == "2":
        print("\nAvailable label XMLs:")
        for i, fname in enumerate(xml_files, start=1):
            print(f"[{i}] {fname}")

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
    else:
        print("Invalid option.")
        return

    if not selected_files:
        print("No valid selections made.")
        return

    try:
        scale_input = input("Enter scale multiplier (e.g. 2 = 2x, 0.5 = shrink): ").strip()
        scale = float(scale_input)
        if scale <= 0:
            raise ValueError
    except ValueError:
        print("Invalid scale multiplier.")
        return

    symbol_bounds = extract_symbol_bounds_from_domdoc(domdoc_path)

    for fname in selected_files:
        full_path = os.path.join(label_folder, fname)
        refine_resize_label_xml(full_path, scale, symbol_bounds)

if __name__ == "__main__":
    main()

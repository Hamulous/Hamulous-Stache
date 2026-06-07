import os
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image

XFL_NS = "http://ns.adobe.com/xfl/2008/"
NS = {"xfl": XFL_NS}
ET.register_namespace("", XFL_NS)

PRECISION = 9


def fnum(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default


def fmt(x):
    return f"{x:.{PRECISION}f}"


def backup_file(src: Path, backup_dir: Path):
    backup_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, backup_dir / src.name)


def tag_local(el: ET.Element) -> str:
    # "{ns}DOMSymbolItem" -> "DOMSymbolItem"
    if "}" in el.tag:
        return el.tag.split("}", 1)[1]
    return el.tag


def get_matrix_element(el: ET.Element):
    return el.find("./xfl:matrix/xfl:Matrix", NS)


def read_matrix(m: ET.Element):
    a = fnum(m.attrib.get("a", "1"), 1.0)
    b = fnum(m.attrib.get("b", "0"), 0.0)
    c = fnum(m.attrib.get("c", "0"), 0.0)
    d = fnum(m.attrib.get("d", "1"), 1.0)
    tx = fnum(m.attrib.get("tx", "0"), 0.0)
    ty = fnum(m.attrib.get("ty", "0"), 0.0)
    return a, b, c, d, tx, ty


def transform_points(a, b, c, d, tx, ty, pts):
    out = []
    for x, y in pts:
        out.append((a * x + c * y + tx, b * x + d * y + ty))
    return out


def bbox_from_points(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def bbox_union(b1, b2):
    if b1 is None:
        return b2
    if b2 is None:
        return b1
    return (min(b1[0], b2[0]), min(b1[1], b2[1]), max(b1[2], b2[2]), max(b1[3], b2[3]))


# -----------------------------
# DOMDocument helpers
# -----------------------------
def parse_domdocument_media_map(domdoc_path: Path):
    """
    Returns mapping:
      media_name -> png_href
    Example:
      "media/buttercup_7x10" -> "media/buttercup_7x10.png"
    """
    media_map = {}
    tree = ET.parse(domdoc_path)
    root = tree.getroot()

    # DOMDocument.xml uses default namespace = XFL_NS
    for item in root.findall(".//xfl:DOMBitmapItem", NS):
        name = item.attrib.get("name")
        href = item.attrib.get("href")
        if name and href:
            media_map[name] = href
    return media_map


def parse_domdocument_includes(domdoc_path: Path):
    """
    Returns list of include hrefs like:
      "image/buttercup_7x10.xml"
      "sprite/face_mark.xml"
    """
    tree = ET.parse(domdoc_path)
    root = tree.getroot()
    out = []
    for inc in root.findall(".//xfl:symbols/xfl:Include", NS):
        href = inc.attrib.get("href")
        if href:
            out.append(href)
    return out


# -----------------------------
# Auto-bounds computation
# -----------------------------
class BoundsComputer:
    def __init__(self, xfl_root: Path, domdoc_path: Path):
        self.xfl_root = xfl_root
        self.domdoc_path = domdoc_path

        self.media_map = parse_domdocument_media_map(domdoc_path)
        self.include_hrefs = parse_domdocument_includes(domdoc_path)

        # Cache
        self.symbol_tree_cache = {}      # symbol_name -> (root_element, path)
        self.symbol_bbox_cache = {}      # symbol_name -> (minx, miny, maxx, maxy)
        self.png_size_cache = {}         # png_path -> (w,h)

    def symbol_xml_path_from_name(self, symbol_name: str) -> Path:
        # symbol_name is like "image/foo" or "sprite/bar"
        return self.xfl_root / "library" / f"{symbol_name}.xml"

    def get_png_size(self, png_rel_href: str):
        # png_rel_href like "media/buttercup_7x10.png"
        png_path = self.xfl_root / "library" / png_rel_href
        if png_path in self.png_size_cache:
            return self.png_size_cache[png_path]
        try:
            with Image.open(png_path) as im:
                size = im.size  # (w,h)
            self.png_size_cache[png_path] = size
            return size
        except Exception:
            self.png_size_cache[png_path] = None
            return None

    def load_symbol_root(self, symbol_name: str):
        if symbol_name in self.symbol_tree_cache:
            return self.symbol_tree_cache[symbol_name][0]

        path = self.symbol_xml_path_from_name(symbol_name)
        if not path.is_file():
            self.symbol_tree_cache[symbol_name] = (None, path)
            return None

        try:
            tree = ET.parse(path)
            root = tree.getroot()
            self.symbol_tree_cache[symbol_name] = (root, path)
            return root
        except Exception:
            self.symbol_tree_cache[symbol_name] = (None, path)
            return None

    def compute_symbol_bbox(self, symbol_name: str):
        """
        Returns bbox in that symbol's LOCAL coordinates: (minx, miny, maxx, maxy)
        Works by walking frames->top-level elements and recursing into nested symbol instances.
        """
        if symbol_name in self.symbol_bbox_cache:
            return self.symbol_bbox_cache[symbol_name]

        root = self.load_symbol_root(symbol_name)
        if root is None:
            self.symbol_bbox_cache[symbol_name] = None
            return None

        bbox = None

        # Iterate frames
        for frame in root.findall(".//xfl:DOMFrame", NS):
            els = frame.find("./xfl:elements", NS)
            if els is None:
                continue

            # top-level only (avoid double scaling / double counting)
            for el in list(els):
                eb = self.compute_element_bbox(el)
                bbox = bbox_union(bbox, eb)

        self.symbol_bbox_cache[symbol_name] = bbox
        return bbox

    def compute_element_bbox(self, el: ET.Element):
        """
        Computes bbox of a single element in its parent's local coords.
        Supports DOMBitmapInstance + DOMSymbolInstance + DOMGroup (basic).
        """
        t = tag_local(el)
        m = get_matrix_element(el)
        if m is None:
            # Some nodes might not have a matrix. Try group members without outer matrix.
            if t == "DOMGroup":
                return self.compute_group_bbox(el, outer_matrix=None)
            return None

        a, b, c, d, tx, ty = read_matrix(m)

        if t == "DOMBitmapInstance":
            media_name = el.attrib.get("libraryItemName")
            if not media_name:
                return None
            png_href = self.media_map.get(media_name)
            if not png_href:
                return None
            size = self.get_png_size(png_href)
            if not size:
                return None
            w, h = size
            pts = [(0, 0), (w, 0), (0, h), (w, h)]
            return bbox_from_points(transform_points(a, b, c, d, tx, ty, pts))

        if t == "DOMSymbolInstance":
            child_name = el.attrib.get("libraryItemName")
            if not child_name:
                return None
            child_bbox = self.compute_symbol_bbox(child_name)
            if not child_bbox:
                return None
            minx, miny, maxx, maxy = child_bbox
            pts = [(minx, miny), (maxx, miny), (minx, maxy), (maxx, maxy)]
            return bbox_from_points(transform_points(a, b, c, d, tx, ty, pts))

        if t == "DOMGroup":
            # group: compute members then apply group matrix
            return self.compute_group_bbox(el, outer_matrix=(a, b, c, d, tx, ty))

        # Unknown element type (shapes etc.) – ignore for now
        return None

    def compute_group_bbox(self, group: ET.Element, outer_matrix=None):
        """
        Basic group support: union member bboxes, then (optionally) transform by outer_matrix.
        """
        bbox = None

        members = group.find("./xfl:members", NS)
        if members is None:
            return None

        for mem in list(members):
            mb = self.compute_element_bbox(mem)
            bbox = bbox_union(bbox, mb)

        if bbox is None:
            return None

        if outer_matrix is None:
            return bbox

        a, b, c, d, tx, ty = outer_matrix
        minx, miny, maxx, maxy = bbox
        pts = [(minx, miny), (maxx, miny), (minx, maxy), (maxx, maxy)]
        return bbox_from_points(transform_points(a, b, c, d, tx, ty, pts))

    def build_center_map(self):
        """
        Precompute centers for all included symbols.
        Returns: { "image/xxx": (cx,cy), "sprite/yyy": (cx,cy), ... }
        """
        centers = {}
        for href in self.include_hrefs:
            # href like "image/buttercup_7x10.xml" -> symbol name "image/buttercup_7x10"
            if not href.lower().endswith(".xml"):
                continue
            symbol_name = href[:-4]
            bbox = self.compute_symbol_bbox(symbol_name)
            if bbox:
                minx, miny, maxx, maxy = bbox
                centers[symbol_name] = ((minx + maxx) / 2.0, (miny + maxy) / 2.0)
        return centers


# -----------------------------
# Resizing label XMLs
# -----------------------------
def scale_instance_keep_center(matrix: ET.Element, s: float, center_local):
    """
    Keep local center point at same world location while scaling.
    t' = P - A'*c
    """
    a, b, c, d, tx, ty = read_matrix(matrix)
    cx, cy = center_local

    Px = a * cx + c * cy + tx
    Py = b * cx + d * cy + ty

    a2, b2, c2, d2 = a * s, b * s, c * s, d * s
    tx2 = Px - (a2 * cx + c2 * cy)
    ty2 = Py - (b2 * cx + d2 * cy)

    matrix.attrib["a"] = fmt(a2)
    matrix.attrib["b"] = fmt(b2)
    matrix.attrib["c"] = fmt(c2)
    matrix.attrib["d"] = fmt(d2)
    matrix.attrib["tx"] = fmt(tx2)
    matrix.attrib["ty"] = fmt(ty2)


def top_level_frame_elements(frame: ET.Element):
    els = frame.find("./xfl:elements", NS)
    if els is None:
        return []
    return list(els)


def resize_label_xml(xml_path: Path, scale: float, center_map: dict, dry_run=False):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    changed = False
    for frame in root.findall(".//xfl:DOMFrame", NS):
        for el in top_level_frame_elements(frame):
            m = get_matrix_element(el)
            if m is None:
                continue

            lib = el.attrib.get("libraryItemName")
            center = center_map.get(lib)

            # If we can't find a center, fall back to registration scaling (still scales, may drift)
            if center is None:
                a, b, c, d, tx, ty = read_matrix(m)
                m.attrib["a"] = fmt(a * scale)
                m.attrib["b"] = fmt(b * scale)
                m.attrib["c"] = fmt(c * scale)
                m.attrib["d"] = fmt(d * scale)
            else:
                scale_instance_keep_center(m, scale, center)

            changed = True

    if dry_run:
        print(f"[DRY] Would resize: {xml_path.name}")
        return

    if changed:
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)
        print(f"Resized: {xml_path.name}")
    else:
        print(f"No changes: {xml_path.name}")


def find_label_xmls(label_folder: Path):
    return sorted([p for p in label_folder.iterdir() if p.is_file() and p.suffix.lower() == ".xml"])


def main():
    xfl_root = Path(input("Drag your .xfl project folder here: ").strip().strip('"'))
    if not xfl_root.is_dir():
        print("Invalid project folder.")
        return

    domdoc_path = xfl_root / "DOMDocument.xml"
    label_folder = xfl_root / "library" / "label"

    if not domdoc_path.is_file():
        print("Missing DOMDocument.xml in project root.")
        return
    if not label_folder.is_dir():
        print("Missing library/label folder.")
        return

    xml_files = find_label_xmls(label_folder)
    if not xml_files:
        print("No label XMLs found.")
        return

    print("\nResize Options:")
    print("[1] Resize all label XMLs")
    print("[2] Select label XMLs")
    opt = input("Choose 1 or 2: ").strip()

    selected = []
    if opt == "1":
        selected = xml_files
    elif opt == "2":
        for i, p in enumerate(xml_files, start=1):
            print(f"[{i}] {p.name}")
        seen = set()
        while True:
            c = input("Enter label number (or 0 to finish): ").strip()
            if c == "0":
                break
            if c.isdigit():
                idx = int(c) - 1
                if 0 <= idx < len(xml_files) and idx not in seen:
                    selected.append(xml_files[idx])
                    seen.add(idx)
                else:
                    print("Invalid index.")
            else:
                print("Enter a number.")
    else:
        print("Invalid option.")
        return

    if not selected:
        print("Nothing selected.")
        return

    try:
        scale = float(input("Enter scale multiplier (e.g. 2, 0.5): ").strip())
        if scale <= 0:
            raise ValueError
    except ValueError:
        print("Invalid scale.")
        return

    dry_run = input("Dry run? (y/n): ").strip().lower() == "y"
    do_backup = (not dry_run) and (input("Backup originals? (y/n): ").strip().lower() != "n")
    backup_dir = xfl_root / "backup_label_xml"

    # Build centers from actual symbol + png geometry (no DOMDocument bounds needed)
    bc = BoundsComputer(xfl_root, domdoc_path)
    center_map = bc.build_center_map()

    if not center_map:
        print("[WARN] Could not compute any symbol centers. Check that library/image/*.xml and library/media/*.png exist.")
    else:
        print(f"[INFO] Computed centers for {len(center_map)} symbols.")

    for p in selected:
        if do_backup:
            backup_file(p, backup_dir)
        resize_label_xml(p, scale, center_map, dry_run=dry_run)


if __name__ == "__main__":
    main()

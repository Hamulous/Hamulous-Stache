import argparse
import re
import shutil
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

# ---------- regex helpers ----------
PVZ2_TXT_RE = re.compile(r"pvz2_([A-Za-z0-9]{2,3})")
PVZ2_BIN_RE = re.compile(rb"pvz2_([A-Za-z0-9]{2,3})")
SAFE_SUFFIX_PATTERN = re.compile(r'(?<![A-Za-z0-9_])pvz2_[A-Za-z0-9]{2,3}(?![A-Za-z0-9_])')

# ---------- utils ----------
def guess_smali_root(decomp: Path, rel: str) -> Path | None:
    for d in ["smali"] + [f"smali_classes{i}" for i in range(1, 10)]:
        p = decomp / d / rel
        if p.exists():
            return p
    return None

def replace_in_text_file(path: Path, pattern: re.Pattern, repl: str) -> bool:
    if not path.exists():
        return False
    txt = path.read_text(encoding="utf-8", errors="ignore")
    new = pattern.sub(repl, txt)
    if new != txt:
        path.write_text(new, encoding="utf-8")
        return True
    return False

# ---------- suffix detection ----------
def detect_suffix_from_text(file_path: Path) -> str | None:
    if not file_path.exists():
        return None
    try:
        m = PVZ2_TXT_RE.search(file_path.read_text(encoding="utf-8", errors="ignore"))
        return m.group(1).lower() if m else None
    except Exception:
        return None

def detect_suffix_from_lib(so_path: Path) -> str | None:
    if not so_path.exists():
        return None
    try:
        data = so_path.read_bytes()
        m = PVZ2_BIN_RE.search(data)
        return m.group(1).decode("ascii").lower() if m else None
    except Exception:
        return None

def detect_donor_suffix(donor_dec: Path) -> str:
    build_root = guess_smali_root(donor_dec, "com/sexyactioncool/lawn")
    if build_root:
        s = detect_suffix_from_text(build_root / "BuildConfig.smali")
        if s:
            return s
    s = detect_suffix_from_text(donor_dec / "AndroidManifest.xml")
    if s:
        return s
    for so in (donor_dec / "lib").rglob("*.so"):
        s = detect_suffix_from_lib(so)
        if s:
            return s
    raise RuntimeError("Could not detect donor pvz2_* suffix (checked BuildConfig, Manifest, libs).")

# ---------- apply suffix ----------
def patch_text_suffixes(base_dec: Path, suffix: str) -> None:
    build_root = guess_smali_root(base_dec, "com/sexyactioncool/lawn")
    if build_root:
        replace_in_text_file(build_root / "BuildConfig.smali", SAFE_SUFFIX_PATTERN, f"pvz2_{suffix}")
    replace_in_text_file(base_dec / "AndroidManifest.xml", SAFE_SUFFIX_PATTERN, f"pvz2_{suffix}")

def patch_lib_suffixes_generic(base_dec: Path, suffix: str) -> None:
    target_len = len(suffix)
    if target_len not in (2, 3):
        print("[i] Donor suffix has unsupported length for binary patch; skipping libs.")
        return

    suffix_bytes = suffix.encode("ascii")
    token_re = re.compile(rb"pvz2_[A-Za-z0-9]{%d}" % target_len)

    count_files = 0
    count_hits = 0

    for so in (base_dec / "lib").rglob("*.so"):
        try:
            data = so.read_bytes()
        except Exception:
            continue

        def repl(m: re.Match) -> bytes:
            nonlocal count_hits
            count_hits += 1
            return b"pvz2_" + suffix_bytes

        new = token_re.sub(repl, data)
        if new != data:
            so.write_bytes(new)
            count_files += 1

    print(f"[+] Binary patch: edited {count_files} .so file(s), replaced {count_hits} token(s).")

# ---------- 60 FPS patch ----------
def enable_60fps(base_dec: Path) -> None:
    root = guess_smali_root(base_dec, "com/popcap/SexyAppFramework")
    if not root:
        print("[i] 60fps: smali root not found; skipped.")
        return
    f = root / "AndroidSurfaceView$AndroidRenderer.smali"
    if not f.exists():
        print("[i] 60fps: AndroidRenderer.smali not found; skipped.")
        return

    txt = f.read_text(encoding="utf-8", errors="ignore")
    new = re.sub(r"const-wide/16\s+v2,\s*0x21", "const-wide/16 v2, 0x10", txt)
    if new != txt:
        f.write_text(new, encoding="utf-8")
        print(f"[+] 60fps patch applied in {f}")
    else:
        print("[i] 60fps: pattern not found (maybe already patched or different version).")

# ---------- name & icon transfer ----------
def _get_or_create_string(root: ET.Element, key: str) -> ET.Element:
    for s in root.findall("string"):
        if s.get("name") == key:
            return s
    # If not present, create it at the end
    elem = ET.Element("string", {"name": key})
    root.append(elem)
    return elem

def transfer_app_strings(donor_dec: Path, base_dec: Path) -> None:
    """
    Copy both app_name and app_label from donor/values/strings.xml into base.
    If base lacks a key, it is created.
    """
    d = donor_dec / "res" / "values" / "strings.xml"
    b = base_dec / "res" / "values" / "strings.xml"
    if not (d.exists() and b.exists()):
        print("[i] strings.xml missing; skipping app_name/app_label transfer.")
        return

    try:
        d_tree = ET.parse(d)
        d_root = d_tree.getroot()
        b_tree = ET.parse(b)
        b_root = b_tree.getroot()

        copied = []

        for key in ("app_name", "app_label"):
            # pull value from donor if present
            val = None
            for s in d_root.findall("string"):
                if s.get("name") == key:
                    val = s.text
                    break
            if val is not None:
                target = _get_or_create_string(b_root, key)
                target.text = val
                copied.append(f"{key}='{val}'")

        if copied:
            b_tree.write(b, encoding="utf-8", xml_declaration=True)
            print("[+] Transferred " + ", ".join(copied))
        else:
            print("[i] Donor had neither app_name nor app_label; nothing to copy.")
    except Exception as e:
        print(f"[i] strings.xml parse/write error; skipping app strings. {e}")

def transfer_icons(donor_dec: Path, base_dec: Path) -> None:
    donor_res = donor_dec / "res"
    base_res = base_dec / "res"
    if not (donor_res.exists() and base_res.exists()):
        print("[i] res folder missing; skipping icons.")
        return
    copied = 0
    for dmm in donor_res.glob("mipmap-*"):
        if dmm.is_dir():
            tgt = base_res / dmm.name
            tgt.mkdir(parents=True, exist_ok=True)
            for f in dmm.glob("*.png"):
                shutil.copy2(f, tgt / f.name)
                copied += 1
    print(f"[+] Icons copied: {copied} file(s).")

# ---------- main ----------
def main():
    parser = argparse.ArgumentParser(
        description="PvZ2 Prefix + Assets Transfer (folder only; no decompile/build)."
    )
    parser.add_argument("--enable-60fps", action="store_true",
                        help="Apply the 60 FPS smali patch (const-wide/16 v2, 0x21 → 0x10).")
    args = parser.parse_args()

    print("=== PvZ2 Prefix + Assets Transfer (folder only) ===")
    base_in  = input('Drag your Snowie APK folder here: ').strip() #I FUCKED UP THESE VALUES TS PMO
    donor_in = input('Drag your Mod\'s APK folder here: ').strip()

    base_dec = Path(base_in.strip('"'))
    donor_dec = Path(donor_in.strip('"'))

    if not base_dec.exists() or not (base_dec / "AndroidManifest.xml").exists():
        sys.exit("Base folder invalid or missing AndroidManifest.xml")
    if not donor_dec.exists() or not (donor_dec / "AndroidManifest.xml").exists():
        sys.exit("Donor folder invalid or missing AndroidManifest.xml")

    # 1) Detect donor suffix once
    donor_suffix = detect_donor_suffix(donor_dec)
    print(f"[+] Detected donor suffix: pvz2_{donor_suffix}")

    # 2) Apply suffix to base (safe text + generic binaries)
    print("[*] Applying suffix in BuildConfig + Manifest (safe)…")
    patch_text_suffixes(base_dec, donor_suffix)

    print("[*] Applying suffix in all lib/*.so binaries…")
    patch_lib_suffixes_generic(base_dec, donor_suffix)

    # 3) Transfer app strings & icons
    print("[*] Transferring app_name and app_label…")
    transfer_app_strings(donor_dec, base_dec)

    print("[*] Transferring icons…")
    transfer_icons(donor_dec, base_dec)

    # 4) Optional 60fps
    if args.enable_60fps:
        print("[*] Applying 60fps patch…")
        enable_60fps(base_dec)
    else:
        yn = input("Enable 60fps now? (y/n): ").strip().lower()
        if yn.startswith("y"):
            print("[*] Applying 60fps patch…")
            enable_60fps(base_dec)

    print("\n[✓] Done. Modified base folder:")
    print(f"    {base_dec}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)

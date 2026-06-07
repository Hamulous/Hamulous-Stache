import datetime
import os
import re
import sys

INNER_CLASS = 'Lcom/snowie/SnowieConfig$1;'
ADD_SIG = 'Ljava/util/ArrayList;->add(Ljava/lang/Object;)Z'

BLOCK_TEMPLATE = (
    '    new-instance v1, {inner}\n'
    '    const-string v2, "{name}"\n'
    '    const v3, {hex_id}\n'
    '    invoke-direct {{v1, v2, v3}}, {inner}-><init>(Ljava/lang/String;I)V\n'
    '    invoke-virtual {{v0, v1}}, {add_sig}\n'
)

def to_hex_literal(id_val: int) -> str:
    if id_val < 0:
        raise ValueError("ID must be non-negative")
    return "0x" + format(id_val, "X")

def load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def save_backup(path: str) -> str:
    base, ext = os.path.splitext(path)
    backup = f"{base}.backup{ext or ''}"
    with open(path, "rb") as src, open(backup, "wb") as dst:
        dst.write(src.read())
    return backup

def find_insertion_region(text: str):
    method_pattern = re.compile(r"(?s)(^\.method.*?^\.end method\s*)", re.MULTILINE)
    candidates = []
    for m in method_pattern.finditer(text):
        block = m.group(0)
        start, end = m.span()
        score = block.count(INNER_CLASS) + block.count(ADD_SIG)
        if score > 0:
            candidates.append((score, start, end))
    if not candidates:
        return (0, len(text))
    candidates.sort(key=lambda x: x[0], reverse=True)
    _, s, e = candidates[0]
    return (s, e)

def find_existing_feature(region_text: str, name: str):
    name_re = re.compile(r'^\s*const-string\s+v2,\s+"{}"\s*$'.format(re.escape(name)), re.MULTILINE)
    m = name_re.search(region_text)
    if not m:
        return None
    name_line_start, name_line_end = m.span()
    after = region_text[name_line_end:]
    v3_re = re.compile(r'^\s*const\s+v3,\s+0x[0-9A-Fa-f]+\s*$', re.MULTILINE)
    m2 = v3_re.search(after)
    if not m2:
        return (name_line_start, name_line_end, -1)
    const_v3_line_start = name_line_end + m2.start()
    return (name_line_start, name_line_end, const_v3_line_start)

def insert_before_last_return(region_text: str, block: str) -> str:
    idx = region_text.rfind("return-object v0")
    if idx == -1:
        return region_text.rstrip() + "\n" + block
    line_start = region_text.rfind("\n", 0, idx) + 1
    return region_text[:line_start] + block + region_text[line_start:]

def apply_change_to_text(full_text: str, feature_name: str, id_val: int):
    hex_lit = to_hex_literal(id_val)
    s, e = find_insertion_region(full_text)
    region = full_text[s:e]

    found = find_existing_feature(region, feature_name)
    if found:
        name_s, name_e, v3_idx = found
        if v3_idx != -1:
            line_end = region.find("\n", v3_idx)
            if line_end == -1:
                line_end = len(region)
            line = region[v3_idx:line_end]
            new_line = re.sub(r'0x[0-9A-Fa-f]+', hex_lit, line)
            if new_line != line:
                region = region[:v3_idx] + new_line + region[line_end:]
                return full_text[:s] + region + full_text[e:], f"updated '{feature_name}' to {hex_lit}"
            return full_text, "no changes"
        else:
            insert_pos = name_e
            new_line = f'    const v3, {hex_lit}\n'
            region = region[:insert_pos] + new_line + region[insert_pos:]
            return full_text[:s] + region + full_text[e:], f"patched missing ID for '{feature_name}'"
    else:
        block = BLOCK_TEMPLATE.format(inner=INNER_CLASS, name=feature_name, hex_id=hex_lit, add_sig=ADD_SIG)
        region_new = insert_before_last_return(region, block)
        if region_new != region:
            region = region_new
            return full_text[:s] + region + full_text[e:], f"inserted '{feature_name}' with {hex_lit}"
        region = region.rstrip() + "\n" + block
        return full_text[:s] + region + full_text[e:], f"appended '{feature_name}' with {hex_lit}"

def parse_id_maybe_hex(s: str) -> int:
    s = s.strip()
    if s.lower().startswith("0x"):
        return int(s, 16)
    try:
        return int(s, 10)
    except ValueError:
        return int(s, 16)

def main():
    raw_path = input("Path to SnowieConfig.smali: ").strip()
    # I FUCKING LOVE STRIPPING QUOTES YEAAAAA
    path = raw_path.strip('"').strip("'")

    if not os.path.isfile(path):
        print(f"[ERROR] File not found: {path}")
        sys.exit(2)

    text = load_text(path)
    pending = []
    while True:
        name = input("Name of New feature (blank to finish): ").strip()
        if not name:
            break
        id_str = input("Id of new feature (decimal or 0xHEX): ").strip()
        try:
            id_val = parse_id_maybe_hex(id_str)
        except Exception:
            print("[WARN] Invalid ID, try again.")
            continue

        new_text, action = apply_change_to_text(text, name, id_val)
        if new_text != text:
            text = new_text
            pending.append(action)
            print(f"- {action}")
        else:
            print(f"[INFO] {action}")

    if not pending:
        print("[INFO] No changes made.")
        return

    backup = save_backup(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"- {len(pending)} change(s) applied.")
    print(f"- Backup saved: {backup}")

    path = input("Path to SnowieConfig.smali: ").strip()
    if not os.path.isfile(path):
        print(f"[ERROR] File not found: {path}")
        sys.exit(2)

    text = load_text(path)
    pending = []
    while True:
        name = input("Name of New feature (blank to finish): ").strip()
        if not name:
            break
        id_str = input("Id of new feature (decimal or 0xHEX): ").strip()
        try:
            id_val = parse_id_maybe_hex(id_str)
        except Exception:
            print("[WARN] Invalid ID, try again.")
            continue

        new_text, action = apply_change_to_text(text, name, id_val)
        if new_text != text:
            text = new_text
            pending.append(action)
            print(f"- {action}")
        else:
            print(f"[INFO] {action}")

    if not pending:
        print("[INFO] No changes made.")
        return

    backup = save_backup(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"- {len(pending)} change(s) applied.")
    print(f"- Backup saved: {backup}")

if __name__ == "__main__":
    main()

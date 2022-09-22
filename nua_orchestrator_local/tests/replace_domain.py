from pathlib import Path

REPLACE = Path("~").expanduser() / "REPLACE_DOMAIN"


def read_changes():
    changes = []
    if not REPLACE.exists():
        return changes
    with open(REPLACE, "r", encoding="utf8") as rfile:
        lines = rfile.read().split("\n")
        for line in lines:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) != 2:
                continue
            changes.append((parts[0], parts[1]))
    return changes


CHANGES = read_changes()


def replace_domain(text: str) -> str:
    for a, b in CHANGES:
        text = text.replace(a, b)
    return text


def replace_file(src_file: Path, tmp_dir: Path | str) -> Path:
    dest_file = Path(tmp_dir) / src_file.name
    with open(src_file, "r", encoding="utf8") as rfile:
        replaced = replace_domain(rfile.read())
        with open(dest_file, "w", encoding="utf8") as wfile:
            wfile.write(replaced)
    return dest_file

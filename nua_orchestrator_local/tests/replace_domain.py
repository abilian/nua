from pathlib import Path

REPLACE = Path("~").expanduser() / "REPLACE_DOMAIN"


def read_changes() -> list:
    changes = []
    if not REPLACE.exists():
        return changes
    lines = REPLACE.read_text(encoding="utf8").split("\n")
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
    source = src_file.read_text(encoding="utf8")
    dest_file.write_text(replace_domain(source), encoding="utf8")
    return dest_file

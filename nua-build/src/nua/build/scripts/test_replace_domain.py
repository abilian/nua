"""Utility script to replace a string in a file, typically 'example.com' to
actual domain in test files.

The original is not changed, but copied with changes made in a second
location.

- args 1: path of textfile containing replacement rules, see example below
- args 2: path of source file
- args 3: directory path for the replaced version of file

replacement rules, put a replacement per line, orig / replacement::

    test.example.com test.yerom.xyz
    test1.example.com test1.yerom.xyz
    test2.example.com test2.yerom.xyz
"""
import sys
from pathlib import Path


def read_changes(rules_file: Path) -> list:
    replacements = []
    if not rules_file.is_file():
        raise FileNotFoundError(rules_file)
    lines = rules_file.read_text(encoding="utf8").split("\n")
    for line in lines:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2:
            continue
        replacements.append((parts[0], parts[1]))
    return replacements


def replace_domain(replacements: list, content: str) -> str:
    for old, new in replacements:
        content = content.replace(old, new)
    return content


def apply_replace(replacements: list, src_file: Path, dest_folder: Path) -> Path:
    dest_file = dest_folder / src_file.name
    content = src_file.read_text(encoding="utf8")
    dest_file.write_text(replace_domain(replacements, content), encoding="utf8")
    return dest_file


def replace_file(
    rules_file: Path | str, src_file: Path | str, dest_folder: Path | str
) -> Path:
    replacements = read_changes(Path(rules_file))
    return apply_replace(replacements, Path(src_file), Path(dest_folder))


def main():
    print(replace_file(sys.argv[1], sys.argv[2], sys.argv[3]))

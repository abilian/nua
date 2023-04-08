"""Utils to fill templates at the start of the container.

Template must be filled :
    - after volume mounts and environment initialization,
    - before application start script.
"""
import os
from pathlib import Path
from typing import Any

from nua.lib.actions import jinja2_render_file


def render_config_templates(data: dict):
    """Find files and templates in the /nua/templates folder and fill them.

    Destination files may be on Docker-mounted volumes.

    This function is expected to be run as root. Files are stored with
    755 rights. Files ending with .j2 are considered as Jinja2
    templates.
    """
    src_folder = Path("/nua/templates")
    if not src_folder.is_dir():
        return
    data.update(os.environ)
    _iterate_template_files(src_folder, data)


def _iterate_template_files(src_folder: Path, data: dict[str, Any]):
    for file in src_folder.rglob("*"):
        if not file.is_file():
            continue
        if file.name.startswith("."):
            continue
        dest = Path("/") / file.relative_to(src_folder)
        if file.name.endswith(".j2"):
            _render_template(file, dest.with_suffix(""), data)
        else:
            _copy_file(file, dest)


def _copy_file(src: Path, dest: Path):
    dest.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    dest.write_bytes(src.read_bytes())
    dest.chmod(0o644)


def _render_template(template: Path, dest: Path, data: dict[str, Any]):
    dest.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    jinja2_render_file(template, dest, data)
    dest.chmod(0o644)

"""Utils to fill templates at the start of the container.

Template must be filled :
    - after volume mounts and environment initialization,
    - before application start script.
"""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nua.lib.actions import jinja2_render_file


def render_config_templates(data: dict[str, Any]):
    templater = Templater(data)
    templater.render_config_templates()


@dataclass
class Templater:
    data: dict[str, Any]

    def render_config_templates(self):
        """Find files and templates in the /nua/templates folder and fill them.

        Destination files may be on Docker-mounted volumes.

        This function is expected to be run as root. Files are stored with
        755 rights. Files ending with .j2 are considered as Jinja2
        templates.
        """
        src_folder = Path("/nua/templates")
        if not src_folder.is_dir():
            return
        self.data.update(os.environ)
        self._iterate_template_files(src_folder)

    def _iterate_template_files(self, src_folder: Path):
        for file in src_folder.rglob("*"):
            if not file.is_file():
                continue
            if file.name.startswith("."):
                continue
            dest = Path("/") / file.relative_to(src_folder)
            if file.name.endswith(".j2"):
                self._render_template(file, dest.with_suffix(""))
            else:
                self._copy_file(file, dest)

    def _copy_file(self, src: Path, dest: Path):
        dest.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        dest.write_bytes(src.read_bytes())
        dest.chmod(0o644)

    def _render_template(self, template: Path, dest: Path):
        dest.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        jinja2_render_file(template, dest, self.data)
        dest.chmod(0o644)

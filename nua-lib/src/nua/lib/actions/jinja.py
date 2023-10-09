from pathlib import Path

from jinja2 import Template

from ..panic import show
from ..tool.state import verbosity


def jinja2_render_file(template: str | Path, dest: str | Path, data: dict):
    """Render a Jinja2 template file."""
    template_path = Path(template)
    if not template_path.is_file():
        raise FileNotFoundError(template_path)

    dest_path = Path(dest)
    j2_template = Template(
        template_path.read_text(encoding="utf8"), keep_trailing_newline=True
    )
    dest_path.write_text(j2_template.render(data), encoding="utf8")
    with verbosity(3):
        show("Jinja2 render template from:", template)


def jinja2_render_from_str_template(template: str, dest: str | Path, data: dict):
    """Render a Jinja2 template from a string."""
    dest_path = Path(dest)
    j2_template = Template(template, keep_trailing_newline=True)
    dest_path.write_text(j2_template.render(data), encoding="utf8")
    with verbosity(3):
        show("Jinja2 render template from string")

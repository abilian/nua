"""Nua scripting: action commands."""
import mmap
import os
import sys
from glob import glob
from pathlib import Path
from typing import Optional

from jinja2 import Template

from .shell import sh


def apt_get_install(packages: list | str) -> None:
    if isinstance(packages, str):
        packages = packages.strip().split()
    if not packages:
        print("apt_get_install(): nothing to install")
        return
    cmd = f"apt-get install -y {' '.join(packages)}"
    sh(cmd)


def build_python(path=None):
    # fixme: improve this
    if not path:
        path = Path()
    requirements = path / "requirements.txt"
    setup_py = path / "setup.py"
    if requirements.exists():
        sh(f"python -m pip install -r {requirements}")
    elif setup_py.exists():
        # assuming code is in src:
        pip_install("src")


def install_package_list(packages: list | str):
    if isinstance(packages, str):
        packages = packages.strip().split()
    if not packages:
        print("install_package_list(): nothing to install")
        return
    environ = os.environ.copy()
    environ["DEBIAN_FRONTEND"] = "noninteractive"
    cmd = f"apt-get update --fix-missing; apt-get install -y {' '.join(packages)}"
    sh(cmd, env=environ, timeout=600)
    sh("apt-get autoremove; apt-get clean", env=environ, timeout=600)


def installed_packages() -> list:
    cmd = "apt list --installed"
    result = sh(cmd, timeout=600, capture_output=True, show_cmd=False)
    return result.splitlines()


def is_python_project():
    if Path("src/requirements.txt").exists():
        return True
    if Path("src/setup.py").exists():
        return True

    return False


def install_nodejs():
    apt_get_install("curl")
    cmd = "curl -sL https://deb.nodesource.com/setup_16.x | bash -"
    sh(cmd)
    apt_get_install("nodejs")
    sh("/usr/bin/npm install -g yarn")


def npm_install(package: str) -> None:
    cmd = f"/usr/bin/npm install -g {package}"
    sh(cmd)


def pip_install(packages: list | str) -> None:
    if isinstance(packages, str):
        packages = packages.strip().split()
    if not packages:
        print("pip_install(): nothing to install")
        return
    cmd = f"python -m pip install {' '.join(packages)}"
    sh(cmd)


def pip_install_glob(pattern: str) -> None:
    packages = [str(f) for f in Path.cwd().glob(pattern)]
    if not packages:
        print("pip_install_glob(): nothing to install")
        return
    cmd = f"python -m pip install {' '.join(packages)}"
    sh(cmd)


def pip_list():
    sh("pip list")


def replace_in(file_pattern: str, string_pattern: str, replace_by: str):
    for file_name in glob(file_pattern, recursive=True):
        path = Path(file_name)
        if not path.is_file():
            continue
        # assuming it's an utf-8 world
        with open(path, encoding="utf-8") as r:
            content = r.read()
            with open(path, mode="w", encoding="utf-8") as w:
                w.write(content.replace(string_pattern, replace_by))


def string_in(file_pattern: str, string_pattern: str) -> list:
    """Return list of Path of files that contains the pattern str string."""
    hit_files = []
    # assuming it's an utf-8 world
    upattern = string_pattern.encode("utf8")
    for file_name in glob(file_pattern, recursive=True):
        path = Path(file_name)
        if not path.is_file():
            continue
        with open(path, "rb", 0) as rfile, mmap.mmap(
            rfile.fileno(), 0, access=mmap.ACCESS_READ
        ) as mfile:
            if mfile.find(upattern) != -1:
                hit_files.append(path)
    return hit_files


def environ_replace_in(str_path: str | Path, env: Optional[dict] = None):
    path = Path(str_path)
    if not path.is_file():
        return
    orig_env = {}
    if env:
        orig_env = dict(os.environ)
        os.environ.update(env)
    try:
        # assuming it's an utf-8 world
        with open(path, encoding="utf8") as rfile:
            content = rfile.read()
        with open(path, mode="w", encoding="utf8") as wfile:
            wfile.write(os.path.expandvars(content))
    except OSError:
        raise
    finally:
        if env:
            os.environ.clear()
            os.environ.update(orig_env)


def jinja2_render_file(template: str | Path, dest: str | Path, data: dict) -> bool:
    template_path = Path(template)
    if not template_path.is_file():
        raise FileNotFoundError(template_path)
    dest_path = Path(dest)
    with open(template_path, encoding="utf8") as rfile:
        template_content = rfile.read()
    j2_template = Template(template_content, keep_trailing_newline=True)
    content = j2_template.render(data)
    with open(dest_path, mode="w", encoding="utf8") as wfile:
        wfile.write(content)
    return True


def check_python_version() -> bool:
    if sys.version_info.major < 3:
        return False
    if sys.version_info.minor < 10:
        return False
    return True

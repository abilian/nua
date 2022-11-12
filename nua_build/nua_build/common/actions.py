"""Nua scripting: action commands."""
import mmap
import os
import sys
from glob import glob
from pathlib import Path

from jinja2 import Template

from .shell import sh


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


def _apt_remove_lists():
    sh("rm -rf /var/lib/apt/lists/*", env=os.environ, timeout=600)


def apt_update():
    environ = os.environ.copy()
    environ["DEBIAN_FRONTEND"] = "noninteractive"
    cmd = "apt-get update --fix-missing"
    sh(cmd, env=environ, timeout=600, show_cmd=False)


def apt_final_clean():
    environ = os.environ.copy()
    environ["DEBIAN_FRONTEND"] = "noninteractive"
    sh("apt-get autoremove; apt-get clean", env=environ, timeout=600, show_cmd=False)


def install_package_list(
    packages: list | str,
    update: bool = True,
    clean: bool = True,
    rm_lists: bool = True,
):
    if isinstance(packages, str):
        packages = packages.strip().split()
    if not packages:
        print("install_package_list(): nothing to install")
        return
    environ = os.environ.copy()
    environ["DEBIAN_FRONTEND"] = "noninteractive"
    update_cmd = "apt-get update --fix-missing; " if update else ""
    cmd = f"{update_cmd}apt-get install --no-install-recommends -y {' '.join(packages)}"
    sh(cmd, env=environ, timeout=600)
    if clean:
        sh("apt-get autoremove; apt-get clean", env=environ, timeout=600)
    if rm_lists:
        _apt_remove_lists()


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


def npm_install(package: str) -> None:
    cmd = f"/usr/bin/npm install -g {package}"
    sh(cmd)


def install_nodejs(version: str = "16.x", rm_lists: bool = True):
    src = f"setup_{version}"
    install_package_list("curl", rm_lists=False)
    cmd = (
        f"curl -sL https://deb.nodesource.com/{src} "
        "| bash - && apt-get install -y nodejs npm"
    )
    sh(cmd)
    if rm_lists:
        _apt_remove_lists()
    npm_install("yarn")


def append_bashrc(home: str | Path, content: str):
    path = Path(home) / ".bashrc"
    if not path.is_file():
        raise FileNotFoundError(path)
    lines = f"# added by Nua script:\n{content}\n\n"
    with open(path, mode="a", encoding="utf8") as wfile:
        wfile.write(lines)


def install_nodejs_via_nvm(home: Path | str = "/nua"):
    """Install nodejs (versions recommaended for Frappe/ERPNext)."""
    node_version_14 = "14.19.3"
    node_version = "16.18.0"
    # nvm_version = "v0.39.0"
    nvm_dir = f"{home}/.nvm"
    install_package_list("wget", rm_lists=False)
    bashrc_modif = (
        f'export PATH="{nvm_dir}/versions/node/v{node_version}/bin/:$PATH"\n'
        f'export NVM_DIR="{nvm_dir}"\n'
        f'[ -s "$NVM_DIR/nvm.sh" ] && source "$NVM_DIR/nvm.sh"\n'
        f'[ -s "$NVM_DIR/bash_completion" ] && source "$NVM_DIR/bash_completion"'
    )
    append_bashrc(home, bashrc_modif)
    os.environ["NVM_DIR"] = ""
    os.environ["HOME"] = str(home)
    cmd = (
        f"wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh "
        f"| bash  && . {nvm_dir}/nvm.sh "
        f"&& nvm install {node_version_14} "
        f"&& nvm use {node_version_14} "
        "&& npm install -g yarn "
        f"&& nvm install {node_version} "
        f"&& nvm use v{node_version} "
        "&& npm install -g yarn "
        f"&& nvm alias default v{node_version} "
        f"&& rm -rf {nvm_dir}/.cache "
    )
    _env = dict(os.environ)
    sh(cmd, env=_env)


def pip_install(packages: list | str, update: bool = False) -> None:
    if isinstance(packages, str):
        packages = packages.strip().split()
    if not packages:
        print("pip_install(): nothing to install")
        return
    option = "-U " if update else " "
    cmd = f"python -m pip install {option}{' '.join(packages)}"
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


def poetry_install(nodev: bool = True) -> None:
    pip_install("poetry pip-autoremove")
    if nodev:
        sh("poetry install --no-dev")
    else:
        sh("poetry install")
    cmd = "pip-autoremove -y poetry"
    sh(cmd)


def replace_in(file_pattern: str, string_pattern: str, replacement: str):
    for file_name in glob(file_pattern, recursive=True):
        path = Path(file_name)
        if not path.is_file():
            continue
        # assuming it's an utf8 world
        content = path.read_text(encoding="utf8")
        path.write_text(content.replace(string_pattern, replacement), encoding="utf8")


def string_in(file_pattern: str, string_pattern: str) -> list:
    """Return list of Path of files that contains the pattern str string."""
    hit_files = []
    # assuming it's an utf8 world
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


def environ_replace_in(str_path: str | Path, env: dict | None = None):
    path = Path(str_path)
    if not path.is_file():
        return
    orig_env = {}
    if env:
        orig_env = dict(os.environ)
        os.environ.update(env)
    try:
        # assuming it's an utf8 world
        content = path.read_text(encoding="utf8")
        path.write_text(os.path.expandvars(content), encoding="utf8")
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
    j2_template = Template(
        template_path.read_text(encoding="utf8"), keep_trailing_newline=True
    )
    dest_path.write_text(j2_template.render(data), encoding="utf8")
    return True


def check_python_version() -> bool:
    """Check that curent python is >=3.10."""
    if sys.version_info.major < 3:
        return False
    if sys.version_info.minor < 10:
        return False
    return True

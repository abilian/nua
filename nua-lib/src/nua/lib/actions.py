"""Nua scripting: action commands."""
import mmap
import os
import re
import sys
import tarfile
import tempfile
from contextlib import contextmanager
from glob import glob
from pathlib import Path
from urllib.request import urlopen

from jinja2 import Template

from .panic import warning
from .shell import sh


#
# Builder for Python projects
#
def is_python_project(path: str | Path = "") -> bool:
    root = Path(path).expanduser().resolve()
    if any(
        (root / f).exists() for f in ("requirements.txt", "setup.py", "pyproject.toml")
    ):
        return True
    return False


def build_python(path: str | Path = ""):
    root = Path(path).expanduser().resolve()
    requirements = root / "requirements.txt"
    setup_py = root / "setup.py"
    if requirements.is_file():
        sh(f"python -m pip install -r {requirements}", cwd=root)
    elif setup_py.is_file():
        sh("python -m pip install", cwd=root)


#
# Other stuff
#
def apt_remove_lists():
    environ = os.environ.copy()
    sh("rm -rf /var/lib/apt/lists/*", env=environ, timeout=600)


def apt_update():
    environ = os.environ.copy()
    environ["DEBIAN_FRONTEND"] = "noninteractive"
    cmd = "apt-get update --fix-missing"
    sh(cmd, env=environ, timeout=600, show_cmd=False)


def apt_final_clean():
    environ = os.environ.copy()
    environ["DEBIAN_FRONTEND"] = "noninteractive"
    cmd = "apt-get autoremove -y; apt-get clean"
    sh(cmd, env=environ, timeout=600)


def _install_packages(packages: list, update: bool):
    if packages:
        environ = os.environ.copy()
        environ["DEBIAN_FRONTEND"] = "noninteractive"
        update_cmd = "apt-get update --fix-missing; " if update else ""
        cmd = f"{update_cmd}apt-get install --no-install-recommends -y {' '.join(packages)}"
        sh(cmd, env=environ, timeout=600)
    else:
        warning("install_package(): nothing to install")


def _purge_packages(packages: list):
    if not packages:
        return
    print(f"Purge packages: {' '.join(packages)}")
    environ = os.environ.copy()
    environ["DEBIAN_FRONTEND"] = "noninteractive"
    for package in packages:
        cmd = f"apt-get purge -y {package} || true"
        sh(cmd, env=environ, timeout=600, show_cmd=False)


def install_package_list(
    packages: list | str,
    update: bool = True,
    clean: bool = True,
    keep_lists: bool = False,
):
    if isinstance(packages, str):
        packages = packages.strip().split()
    _install_packages(packages, update)
    if clean:
        apt_final_clean()
    if not keep_lists:
        apt_remove_lists()


def purge_package_list(packages: list | str):
    if isinstance(packages, str):
        packages = packages.strip().split()
    _purge_packages(packages)
    apt_final_clean()


@contextmanager
def tmp_install_package_list(
    packages: list | str,
    update: bool = True,
    keep_lists: bool = False,
):
    if isinstance(packages, str):
        packages = packages.strip().split()
    _install_packages(packages, update)
    try:
        yield
    finally:
        _purge_packages(packages)
        apt_final_clean()
        if not keep_lists:
            apt_remove_lists()


def installed_packages() -> list:
    cmd = "apt list --installed"
    result = sh(cmd, timeout=600, capture_output=True, show_cmd=False)
    return result.splitlines()


def npm_install(package: str, force: bool = False) -> None:
    opt = " --force" if force else ""
    cmd = f"/usr/bin/npm install -g{opt} {package}"
    sh(cmd)


def install_nodejs(version: str = "16.x", keep_lists: bool = False):
    purge_package_list("yarn npm nodejs")
    url = f"https://deb.nodesource.com/setup_{version}"
    target = Path("/nua") / "install_node.sh"
    with urlopen(url) as remote:  # noqa S310
        target.write_bytes(remote.read())
    cmd = "bash /nua/install_node.sh"
    sh(cmd)
    cmd = "apt-get install -y nodejs"
    sh(cmd)
    cmd = "/usr/bin/npm update -g npm"
    sh(cmd)
    cmd = "/usr/bin/npm install -g --force yarn"
    sh(cmd)
    if not keep_lists:
        apt_remove_lists()


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
    install_package_list("wget", keep_lists=True)
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
    environ = os.environ.copy()
    sh(cmd, env=environ)


def pip_install(packages: list | str, update: bool = False) -> None:
    if isinstance(packages, str):
        packages = packages.strip().split()
    if not packages:
        warning("pip_install(): nothing to install")
        return
    option = "-U " if update else " "
    cmd = f"python -m pip install {option}{' '.join(packages)}"
    sh(cmd)


def pip_install_glob(pattern: str) -> None:
    packages = [str(f) for f in Path.cwd().glob(pattern)]
    if not packages:
        warning("pip_install_glob(): nothing to install")
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


def install_mariadb_python(version: str = "1.1.4"):
    """Connector for MariaDB."""
    install_package_list(
        [
            "python3-dev",
            "libmariadb3",
            "libmariadb-dev",
            "mariadb-client",
            "unzip",
            "build-essential",
        ]
    )
    with tempfile.TemporaryDirectory(dir="/var/tmp") as tmpdirname:  # noqa S108
        cmd = f"python -m pip download mariadb=={version}"
        result = sh(cmd, cwd=tmpdirname, capture_output=True)
        saved_file = re.search("Saved(.*)\n", result).group(1).strip()  # type: ignore
        archive = Path(saved_file).name
        stem = Path(archive).stem
        if stem.endswith(".tar"):
            stem = Path(stem).stem
        if archive.endswith("zip"):
            unzip = f"unzip {archive}"  # for 1.1.4
        else:
            unzip = f"tar xzf {archive}"  # for 1.1.5.post2
        cmd = (
            f"{unzip} "
            f"&& cd {stem} && python setup.py bdist_wheel && mv dist/*.whl .."
        )
        sh(cmd, cwd=tmpdirname)
        pip_install_glob(f"tmpdirname/{stem}*.whl")
    purge_package_list("build-essential unzip")


def install_mariadb_1_1_5():
    """Connector for MariaDB, since version 1.1.5post3."""
    install_package_list("libmariadb3 mariadb-client", keep_lists=True)
    with tmp_install_package_list("libmariadb-dev python3-dev build-essential"):
        pip_install("mariadb")


def install_psycopg2_python():
    """Connector for PostgreSQL."""
    install_package_list("libpq-dev")
    pip_install("psycopg2-binary")


def download_extract(url: str, dest: str | Path) -> Path:
    name = Path(url).name
    if not any(name.endswith(suf) for suf in (".zip", ".tar", ".tar.gz", ".tgz")):
        raise ValueError(f"Unknown archive format for '{name}'")
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / name
        with urlopen(url) as remote:  # noqa S310
            target.write_bytes(remote.read())
        # if name.endswith(".zip"):
        #     return extract_zip(target, dest)
        return extract_all(target, dest)


def extract_all(archive: str | Path, dest: str | Path) -> Path:
    with tarfile.open(archive) as tar:
        tar.extractall(dest)
    name = Path(archive).stem
    if name.endswith(".tar"):
        name = name[:-4]
    result = Path(dest) / name
    if not result.exists():
        name = re.sub(r"-[0-9\.post]*$", "", name)
        result = Path(dest) / name
    if not result.exists():
        warning(f"expected '{result}' not found")
    return result


#
# String and replacement utils
#
def set_php_ini_keys(replacements: dict, path: str | Path):
    path = Path(path)
    content = path.read_text()
    for key, value in replacements.items():
        content = re.sub(rf"^;*\s*{key}\s*=", f"{key} = {value}", content, flags=re.M)
    path.write_text(content)


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
        orig_env = os.environ.copy()
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


def snake_format(name: str) -> str:
    return "_".join(word.lower() for word in name.replace("-", "_").split("_"))


def camel_format(name: str) -> str:
    return "".join(word.title() for word in name.replace("-", "_").split("_"))

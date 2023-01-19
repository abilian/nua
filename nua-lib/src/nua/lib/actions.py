"""Nua scripting: action commands."""
import importlib.util
import mmap
import os
import re
import sys
import tarfile
import tempfile
from contextlib import contextmanager
from glob import glob
from importlib import resources as rso
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

from jinja2 import Template

from .backports import chdir
from .panic import info, show, warning
from .shell import sh
from .tool.state import verbosity

LONG_TIMEOUT = 1800
SHORT_TIMEOUT = 300


#
# Builder for Python projects
#
def is_python_project(path: str | Path = "") -> bool:
    root = Path(path).expanduser().resolve()
    deps_files = ("requirements.txt", "setup.py", "pyproject.toml")
    result = any((root / f).exists() for f in deps_files)
    if verbosity(2):
        info("is_python_project:", result)
    return result


def build_python(path: str | Path = ""):
    root = Path(path).expanduser().resolve()
    requirements = root / "requirements.txt"
    pyproject = root / "pyproject.toml"
    setup_py = root / "setup.py"
    if requirements.is_file():
        sh(f"python -m pip install -r {requirements} .", cwd=root)
    elif setup_py.is_file() or pyproject.is_file():
        sh("python -m pip install .", cwd=root)
    else:
        warning(f"No method found to build the python project in '{root}'")


#
# Other stuff
#
def install_meta_packages(packages: list, keep_lists: bool = False):
    if "psycopg2" or "postgres-client" in packages:
        info("install meta package: psycopg2")
        install_psycopg2_python(keep_lists=keep_lists)
    if "mariadb-client" in packages:
        info("install meta package: mariadb-client")
        install_mariadb_1_1_5(keep_lists=keep_lists)


def install_packages(packages: list, keep_lists: bool = False):
    if packages:
        if verbosity(2):
            show("install packages")
        install_package_list(packages, keep_lists=keep_lists)


@contextmanager
def install_build_packages(
    packages: list | str,
    update: bool = True,
    keep_lists: bool = False,
):
    if isinstance(packages, str):
        packages = packages.strip().split()
    if packages:
        if verbosity(2):
            show("install temporary build packages")
        _install_packages(packages, update)
    try:
        yield
    finally:
        if packages:
            if verbosity(2):
                show("remove temporary build packages")
            _purge_packages(packages)
        apt_final_clean()
        if not keep_lists:
            apt_remove_lists()


def install_pip_packages(packages: list | str | None = None):
    if not packages:
        return
    if isinstance(packages, str):
        packages = packages.strip().split()
    show("Installing pip packages declared in nua-config")
    pip_install(_glob_extended(packages))


def _glob_extended(packages: list):
    extended = []
    for package in packages:
        if not package:
            continue
        if "*" not in package:
            extended.append(package)
            continue
        glob_result = [str(f) for f in Path.cwd().glob(package)]
        if not glob_result:
            warning("glob() got empty result:")
            info("    glob path:", Path.cwd())
            info("    glob pattern:", package)
        extended.extend(glob_result)
    return extended


def apt_remove_lists():
    environ = os.environ.copy()
    sh("rm -rf /var/lib/apt/lists/*", env=environ, timeout=SHORT_TIMEOUT)


def apt_update():
    environ = os.environ.copy()
    environ["DEBIAN_FRONTEND"] = "noninteractive"
    cmd = "apt-get update --fix-missing"
    sh(cmd, env=environ, timeout=LONG_TIMEOUT, show_cmd=False)


def apt_final_clean():
    environ = os.environ.copy()
    environ["DEBIAN_FRONTEND"] = "noninteractive"
    cmd = "apt-get autoremove -y; apt-get clean"
    sh(cmd, env=environ, timeout=SHORT_TIMEOUT)


def _install_packages(packages: list, update: bool):
    if packages:
        environ = os.environ.copy()
        environ["DEBIAN_FRONTEND"] = "noninteractive"
        cmd = "apt-get update --fix-missing; " if update else ""
        cmd += f"apt-get install --no-install-recommends -y {' '.join(packages)}"
        sh(cmd, env=environ, timeout=LONG_TIMEOUT)
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
        sh(cmd, env=environ, timeout=SHORT_TIMEOUT, show_cmd=False)


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
    result = sh(cmd, timeout=SHORT_TIMEOUT, capture_output=True, show_cmd=False)
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
        sh("poetry install --only main")
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


def install_mariadb_1_1_5(keep_lists=True):
    """Connector for MariaDB, since version 1.1.5post3."""
    install_package_list("libmariadb3 mariadb-client", keep_lists=keep_lists)
    with tmp_install_package_list(
        "libmariadb-dev python3-dev build-essential", keep_lists=True
    ):
        pip_install("mariadb")


def install_psycopg2_python(keep_lists: bool = False):
    """Connector for PostgreSQL."""
    install_package_list(["libpq-dev"], keep_lists=keep_lists)
    pip_install("psycopg2-binary")


def download_extract(url: str, dest: str | Path) -> Path | None:
    name = Path(url).name
    if not any(name.endswith(suf) for suf in (".zip", ".tar", ".tar.gz", ".tgz")):
        raise ValueError(f"Unknown archive format for '{name}'")
    if verbosity(2):
        info("download URL:", url)
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / name
        with urlopen(url) as remote:  # noqa S310
            target.write_bytes(remote.read())
        # if name.endswith(".zip"):
        #     return extract_zip(target, dest)
        return extract_all(target, dest, url)


def extract_all(archive: str | Path, dest: str | Path, url: str = "") -> Path | None:
    if verbosity(2):
        info("extract archive:", archive)
    with tarfile.open(archive) as tar:
        tar.extractall(dest)
    name = Path(archive).stem
    if name.endswith(".tar"):
        name = name[:-4]

    possible = [name]

    name2 = re.sub(r"-[0-9.post]*$", "", name)
    if name2:
        possible.append(name2)

    if url:
        if match := re.search(".*/(.*)/archive/.*", url):
            possible.append(match.group(1))
        version = re.sub(r".*-([0-9.post]*$)", "", name)
        if version:
            possible.extend([f"{n}-{version}" for n in possible])
            possible.append(version)
    return _detect_archive_path(dest, possible)


def _detect_archive_path(dest: str | Path, possible: list) -> Path | None:
    for name in possible:
        result = Path(dest) / name
        if result.exists():
            if verbosity(2):
                info("detected path:", result)
            return result
    if verbosity(2):
        show("detected path: no path detected")
    return None


def is_local_dir(project: str) -> bool:
    """Analysis of some ptoject string and guess wether local path or URL.
    (WIP)
    """
    parsed = urlparse(project)
    if parsed.scheme:
        # guess it is a download URL
        result = False
    else:
        abs_path = Path(project).absolute().resolve()
        result = abs_path.is_dir()
    if verbosity(2):
        info("is_local_dir", abs_path, result)
    return result


def project_path(project: str) -> Path | None:
    """Guess meaning of project string and send back local path of the project.
    (WIP)
    """
    if is_local_dir(project):
        return Path(project)
    return download_extract(project, "/nua/build")


def project_install(project: str) -> None:
    path = project_path(project)
    if not path:
        warning(f"No path found for project '{project}'")
        return
    detect_and_install(path)


def detect_and_install(directory: str | Path | None) -> None:
    if directory:
        path = Path(directory)
    else:
        path = Path(".")
    if verbosity(2):
        info("detect_and_install", path)
    with chdir(path):
        if is_python_project():
            build_python()
            return
        warning(f"Not a known project type in '{path}'")


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
    if verbosity(2):
        show(f"replace_in() '{string_pattern}' by '{replacement}'")
    counter = 0
    for file_name in glob(file_pattern, recursive=True):
        path = Path(file_name)
        if not path.is_file():
            continue
        # assuming it's an utf8 world
        content = path.read_text(encoding="utf8")
        path.write_text(content.replace(string_pattern, replacement), encoding="utf8")
        counter += 1
    if verbosity(2):
        show(f"replace_in() done in {counter} files")


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
    if verbosity(2):
        show("jinja2 render:", template)
    return True


def jinja2_render_from_str_template(
    template: str, dest: str | Path, data: dict
) -> bool:
    dest_path = Path(dest)
    j2_template = Template(template, keep_trailing_newline=True)
    dest_path.write_text(j2_template.render(data), encoding="utf8")
    if verbosity(2):
        show("jinja2 render from string")
    return True


def check_python_version() -> bool:
    """Check that curent python is >=3.10."""
    return sys.version_info >= (3, 10)


def python_package_installed(pkg_name: str) -> bool:
    """Utility to test if a python package is installed.

    Nota: replaced by some function using importlib.
    """
    return bool(importlib.util.find_spec(pkg_name))


def snake_format(name: str) -> str:
    return "_".join(word.lower() for word in name.replace("-", "_").split("_"))


def camel_format(name: str) -> str:
    return "".join(word.title() for word in name.replace("-", "_").split("_"))


def copy_from_package(package: str, filename: str, destdir: Path):
    content = rso.files(package).joinpath(filename).read_text(encoding="utf8")
    target = destdir / filename
    target.write_text(content)

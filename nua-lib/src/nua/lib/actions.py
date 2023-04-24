"""Nua scripting: action commands."""
import importlib.util
import mmap
import os
import re
import sys
import tempfile
from collections.abc import Iterable
from contextlib import contextmanager
from glob import glob
from hashlib import sha256
from importlib import resources as rso
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

from jinja2 import Template

from .backports import chdir
from .panic import Abort, info, show, warning
from .shell import chown_r, sh
from .tool.state import packages_updated, set_packages_updated, verbosity
from .unarchiver import unarchive

LONG_TIMEOUT = 1800
SHORT_TIMEOUT = 300


#
# Builder for Python projects
#
def build_python(path: str | Path = "", user: str = ""):
    root = Path(path).expanduser().resolve()
    requirements = root / "requirements.txt"
    pyproject = root / "pyproject.toml"
    setup_py = root / "setup.py"
    if user:
        prefix = f"sudo -nu {user} "
    else:
        prefix = ""
    if requirements.is_file():
        sh(f"{prefix}python -m pip install -r {requirements} .", cwd=root)
    elif setup_py.is_file() or pyproject.is_file():
        sh(f"{prefix}python -m pip install .", cwd=root)
    else:
        warning(f"No method found to build the python project in '{root}'")


#
# Other stuff
#
def install_meta_packages(packages: list, keep_lists: bool = False):
    if "psycopg2" in packages or "postgres-client" in packages:
        info("install meta package: psycopg2")
        install_psycopg2_python(keep_lists=keep_lists)
    if "mariadb-client" in packages:
        info("install meta package: mariadb-client")
        install_mariadb_1_1_5(keep_lists=keep_lists)


def install_packages(packages: list, keep_lists: bool = False):
    if packages:
        with verbosity(2):
            show("install packages")
        install_package_list(packages, keep_lists=keep_lists)


@contextmanager
def install_build_packages(
    packages: list | str,
    keep_lists: bool = False,
    installed: Iterable[str] | None = None,
):
    success = True
    if installed:
        already = set(installed)
    else:
        already = set()
    if isinstance(packages, str):
        packages = packages.strip().split()
    needed = [package for package in packages if package not in already]
    if needed:
        with verbosity(2):
            show("Install temporary build packages")
        _install_packages(needed)
    try:
        yield
    except SystemExit:
        success = False
        raise
    finally:
        if success:
            if needed:
                with verbosity(2):
                    show("Remove temporary build packages")
                _purge_packages(needed)
            apt_final_clean()
            if not keep_lists:
                apt_remove_lists()


def install_python(version: str = "3.10", venv: str = "", keep_lists: bool = False):
    PY_UBUNTU = {"2.7", "3.10"}
    PY_DEADSNAKES = {"3.7", "3.8", "3.9", "3.11"}
    if version not in PY_UBUNTU and version not in PY_DEADSNAKES:
        raise Abort(f"Unknown Python version: '{version}'")

    if not venv:
        venv = f"/nua/p{version.replace('.','')}"
    if version in PY_DEADSNAKES:
        sh("add-apt-repository -y ppa:deadsnakes/ppa")
    _install_python_packages(version)
    _make_python_venv(version, venv)
    chown_r(venv, "nua")
    if not keep_lists:
        apt_remove_lists()


def _install_python_packages(version: str):
    py = f"python{version}"
    if version == "2.7":
        packages = [
            "software-properties-common",
            py,
            f"{py}-dev",
            "virtualenv",
            "python-pip",
            f"{py}-distutils",
        ]
    else:
        packages = [
            "software-properties-common",
            py,
            f"{py}-dev",
            f"{py}-venv",
            f"{py}-distutils",
        ]
    _install_packages(packages)


def _venv_environ(venv: str) -> dict[str, str]:
    env = os.environ.copy()
    env["VIRTUAL_ENV"] = venv
    env["PATH"] = f"{venv}/bin:{env['PATH']}"
    return env


def _make_python_venv(version: str, venv: str):
    if version == "2.7":
        return _make_python_venv_27(venv)
    py = f"python{version}"
    sh(f"{py} -m venv {venv}")
    with python_venv(venv):
        sh("python -m pip install --upgrade setuptools wheel pip")


def _make_python_venv_27(venv: str):
    sh(f"virtualenv -p /usr/bin/python2.7 {venv}")
    with python_venv(venv):
        sh("pip2 install -U setuptools wheel pip")


@contextmanager
def python_venv(venv: str):
    orig_env = dict(os.environ)
    os.environ["VIRTUAL_ENV"] = venv
    os.environ["PATH"] = f"{venv}/bin:{orig_env['PATH']}"
    with verbosity(2):
        print(f"Using Python venv: '{venv}'")
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(orig_env)


def install_pip_packages(packages: list | str | None = None) -> bool:
    if not packages:
        return False
    if isinstance(packages, str):
        packages = packages.strip().split()
    show("Installing pip packages declared in nua-config")
    return pip_install(_glob_extended(packages))


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
    set_packages_updated(False)


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


def _install_packages(packages: list):
    if packages:
        environ = os.environ.copy()
        environ["DEBIAN_FRONTEND"] = "noninteractive"
        if not packages_updated():
            cmd = "apt-get update --fix-missing; "
        else:
            cmd = ""
        cmd += f"apt-get install --no-install-recommends -y {' '.join(packages)}"
        sh(cmd, env=environ, timeout=LONG_TIMEOUT)
        set_packages_updated(True)
    else:
        warning("install_package(): nothing to install")


def _purge_packages(packages: list):
    if not packages:
        return
    print(f"Purge packages: {' '.join(packages)}")
    environ = os.environ.copy()
    environ["DEBIAN_FRONTEND"] = "noninteractive"
    for package in packages:
        cmd = f"apt-get purge -y {package} 2>/dev/null || true"
        sh(cmd, env=environ, timeout=SHORT_TIMEOUT, show_cmd=False)


def install_package_list(
    packages: list | str,
    clean: bool = True,
    keep_lists: bool = False,
):
    if isinstance(packages, str):
        packages = packages.strip().split()
    _install_packages(packages)
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
    keep_lists: bool = True,
):
    if isinstance(packages, str):
        packages = packages.strip().split()
    _install_packages(packages)
    try:
        yield
    finally:
        _purge_packages(packages)
        apt_final_clean()
        if not keep_lists:
            apt_remove_lists()


def installed_packages() -> set[str]:
    cmd = "apt list --installed"
    result = sh(cmd, timeout=SHORT_TIMEOUT, capture_output=True, show_cmd=False)
    return {name.split("/")[0] for name in str(result).splitlines()}


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
    for cmd in (
        "bash /nua/install_node.sh",
        "apt-get install -y nodejs",
        "/usr/bin/npm update -g npm",
        "/usr/bin/npm install -g --force yarn",
        "/usr/bin/npm install -g --force node-gyp",
    ):
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
    install_package_list("wget ", keep_lists=True)
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


def compile_openssl_1_1() -> str:
    soft = "openssl-1.1.1g"
    info(f"Compiling {soft}")
    dest = f"/nua/.openssl/{soft}"
    install_package_list(
        "wget pkg-config build-essential",
        keep_lists=True,
        clean=False,
    )
    with chdir("/nua"):
        sh(f"wget https://www.openssl.org/source/{soft}.tar.gz")
        sh(f"tar zxvf {soft}.tar.gz")
        with chdir(soft):
            sh(f"./config --prefix={dest} --openssldir={dest}")
            # ../test/recipes/80-test_ssl_new.t (Wstat: 256 Tests: 29 Failed: 1)
            # Failed test:  12
            # sh("make && make test && make install")
            sh("make -j4 && make install_sw && make install_ssldirs")
            sh(f"rm -fr {dest}/certs")
            sh(f"ln -s /etc/ssl/certs {dest}/certs")
        sh(f"rm -fr {soft}")
        sh(f"rm -f {soft}.tar.gz")
    return dest


def install_ruby(
    version: str = "3.2.1",
    keep_lists: bool = False,
):
    """Installation of Ruby via 'ruby-install'.

    Exec as root.
    """
    install_package_list(
        "wget pkg-config build-essential libpq-dev",
        keep_lists=True,
        clean=False,
    )
    purge_package_list("ruby ruby-dev ri")
    options = "--disable-install-doc"
    if version.startswith("2.") or version.startswith("3.0"):
        ssl = compile_openssl_1_1()
        options = f"--disable-install-doc --with-openssl-dir={ssl}"
    ri_vers = "0.9.0"
    with chdir("/tmp"):  # noqa s108
        cmd = (
            f"wget -O ruby-install-{ri_vers}.tar.gz "
            f"https://github.com/postmodern/ruby-install/archive/v{ri_vers}.tar.gz"
        )
        sh(cmd)
        cmd = f"tar -xzvf ruby-install-{ri_vers}.tar.gz"
        sh(cmd)
        with chdir(f"ruby-install-{ri_vers}"):
            cmd = "make install"
            sh(cmd)
    cmd = f"rm -fr /tmp/ruby-install-{ri_vers}*"
    sh(cmd)
    cmd = f"ruby-install --system --cleanup -j4 {version} -- {options}"
    sh(cmd)
    cmd = f"ruby-install --system --cleanup -j4 {version} -- {options}"
    sh(cmd)
    if not keep_lists:
        apt_remove_lists()


def pip_install(
    packages: list | str,
    update: bool = False,
    user: str = "",
) -> bool:
    if isinstance(packages, str):
        packages = packages.strip().split()
    if not packages:
        warning("pip_install(): nothing to install")
        return False
    option = "-U " if update else " "
    if user:
        prefix = f"sudo -nu {user} "
    else:
        prefix = ""
    cmd = f"{prefix}python -m pip install {option}{' '.join(packages)}"
    sh(cmd)
    return True


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
        ],
        keep_lists=True,
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


def install_psycopg2_python(keep_lists: bool = True):
    """Connector for PostgreSQL."""
    install_package_list(["libpq-dev"], keep_lists=keep_lists)
    pip_install("psycopg2-binary")


def download_extract(
    url: str,
    dest: str | Path,
    dest_name: str,
    checksum: str = "",
) -> Path:
    name = Path(url).name
    with verbosity(2):
        print("Download URL:", url)
        # info("Download URL:", url)
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / name
        with urlopen(url) as remote:  # noqa S310
            target.write_bytes(remote.read())
        verify_checksum(target, checksum)
        dest_path = Path(dest) / dest_name
        unarchive(target, str(dest_path))
        with verbosity(2):
            print("Project path:", dest_path)
        with verbosity(3):
            sh(f"ls -l {dest_path}")
        return dest_path


def verify_checksum(target: Path, checksum: str) -> None:
    """If a checksum is provided, verify that the Path has the same sha256
    hash.

    Abort the programm if hashes differ. Currently supporting only
    sha256.
    """
    if not checksum:
        return
    # Assuming checksum is a 64-long string verified by Nua-config
    file_hash = sha256(target.read_bytes()).hexdigest()
    if file_hash == checksum:
        with verbosity(2):
            show("Checksum of dowloaded file verified")
    else:
        raise Abort(
            f"Wrong checksum verification for file:\n{target}\n"
            f"Computed sha256 sum: {file_hash}\nExpected result:     {checksum}"
        )


def is_local_dir(project: str) -> bool:
    """Analysis of some ptoject string and guess wether local path or URL.

    (WIP)
    """
    parsed = urlparse(project)
    if parsed.scheme:
        # guess it is a download URL
        result = False
        abs_path_s = ""
    else:
        abs_path = Path(project).absolute().resolve()
        result = abs_path.is_dir()
        abs_path_s = str(abs_path)
    with verbosity(3):
        info(f"is_local_dir '{abs_path_s}'", result)
    return result


def install_source(
    url: str,
    dest_dir: str | Path,
    name: str,
    checksum: str = "",
) -> Path:
    """Guess meaning of url string and send back local path of the dowloaded
    source.

    (WIP)
    """
    if is_local_dir(url):
        return Path(url).resolve()
    return download_extract(url, dest_dir, name, checksum)


def install_git_source(
    url: str,
    branch: str,
    dest_dir: str | Path,
    name: str,
) -> Path:
    """Git clone a remote repository."""
    if dest_dir:
        path = Path(dest_dir).resolve()
    else:
        path = Path(".").resolve()
    cmd = f"git clone --depth 1 --branch {branch} {url} {name}"
    if "git" in installed_packages():
        with chdir(path):
            sh(cmd)
    else:
        with tmp_install_package_list("git"), chdir(path):
            sh(cmd)
    return path / name


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
    with verbosity(2):
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
    with verbosity(2):
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
    with verbosity(3):
        show("Jinja2 render template from:", template)
    return True


def jinja2_render_from_str_template(
    template: str, dest: str | Path, data: dict
) -> bool:
    dest_path = Path(dest)
    j2_template = Template(template, keep_trailing_newline=True)
    dest_path.write_text(j2_template.render(data), encoding="utf8")
    with verbosity(3):
        show("Jinja2 render template from string")
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


def copy_from_package(
    package: str,
    filename: str,
    destdir: Path,
    destname: str = "",
):
    content = rso.files(package).joinpath(filename).read_text(encoding="utf8")
    if destname:
        target = destdir / destname
    else:
        target = destdir / filename
    target.write_text(content)

from pathlib import Path

from ..backports import chdir
from ..panic import info
from ..shell import sh
from .apt import install_package_list, installed_packages, tmp_install_package_list
from .python import pip_install
from .util import download_extract, is_local_dir


def install_meta_packages(packages: list, keep_lists: bool = False):
    """Install meta packages."""
    if "psycopg2" in packages or "postgres-client" in packages:
        info("install meta package: psycopg2")
        install_psycopg2_python(keep_lists=keep_lists)
    if "mariadb-client" in packages:
        info("install meta package: mariadb-client")
        install_mariadb_1_1_5(keep_lists=keep_lists)


def compile_openssl_1_1() -> str:
    """Compile OpenSSL 1.1.x.

    Returns:
        str: The path to the compiled OpenSSL.
    """
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


def install_mariadb_1_1_5(keep_lists=True):
    """Python connector for MariaDB, since version 1.1.5post3."""
    install_package_list("libmariadb3 mariadb-client", keep_lists=keep_lists)
    with tmp_install_package_list(
        "libmariadb-dev python3-dev build-essential", keep_lists=True
    ):
        pip_install("mariadb")


def install_psycopg2_python(keep_lists: bool = True):
    """Python connector for PostgreSQL."""
    install_package_list(["libpq-dev"], keep_lists=keep_lists)
    pip_install("psycopg2-binary")


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


def install_git_source(url: str, branch: str, dest_dir: str | Path) -> Path:
    """Install a project from git source."""
    if dest_dir:
        path = Path(dest_dir).resolve()
    else:
        path = Path(".").resolve()
    url = url.strip()
    if url.endswith(".git"):
        url = url[:-4]
    name = url.split("/")[-1]
    cmd = f"git clone --depth 1 --branch {branch} {url} {name}"
    if "git" in installed_packages():
        with chdir(path):
            sh(cmd)
    else:
        with tmp_install_package_list("git"), chdir(path):
            sh(cmd)
    return path / name

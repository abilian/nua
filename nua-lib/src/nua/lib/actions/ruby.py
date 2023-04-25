from ..backports import chdir
from ..shell import sh
from .apt import apt_remove_lists, install_package_list, purge_package_list
from .misc import compile_openssl_1_1


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

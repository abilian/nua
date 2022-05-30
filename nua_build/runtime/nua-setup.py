#!/bin/env python3

import os
import sys

os.environ["DEBIAN_FRONTEND"] = "noninteractive"

PACKAGES = [
    # Python stuff needed for nua
    "python3-pip",
    "python3-venv",
    "python3-toml",
    "python3-dev",
    "python3-wheel",
    # Stuff
    "apt-utils",
    # Web stuff
    "ca-certificates",
    "curl",
    # Build stuff
    "software-properties-common",
    "build-essential",
    "make",
    "gcc",
    "g++",
    "git",
    # DB stuff
    "libmysqlclient-dev",
]

PY_PACKAGES = [
    "fire",
    "rich",
]

#### utils:


def is_python_project():
    if Path("src/requirements.txt").exists():
        return True
    if Path("src/setup.py").exists():
        return True

    return False


# Copied from from boltons.fileutils
def mkdir_p(path):
    """Creates a directory and any parent directories that may need to
    be created along the way, without raising errors for any existing
    directories. This function mimics the behavior of the ``mkdir -p``
    command available in Linux/BSD environments, but also works on
    Windows.
    """
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            return
        raise
    return


def rm_rf(path: str):
    if Path(path).exists():
        shutil.rmtree(path)


def panic(msg: str, status: int = 1):
    print(msg)
    sys.exit(status)


def sh(cmd: str):
    print(cmd)
    try:
        status = call(cmd, shell=True)
        if status < 0:
            panic(f"Child was terminated by signal {-status}", status)
        elif status > 0:
            panic("Something went wrong", status)
    except OSError as e:
        panic(f"Execution failed: {e}")


def echo(text: str, filename: str) -> None:
    with open(filename, "w") as fd:
        fd.write(text)


#############################################################


def main():
    configure_apt()
    install_native_packages()
    install_python()
    install_nodejs()


def configure_apt():
    echo("Acquire::http {No-Cache=True;};", "/etc/apt/apt.conf.d/no-cache")
    echo(
        'APT::Install-Recommends "0"; APT::Install-Suggests "0";',
        "/etc/apt/apt.conf.d/01norecommend",
    )
    echo('Dir::Cache { srcpkgcache ""; pkgcache ""; }', "/etc/apt/apt.conf.d/02nocache")
    echo(
        'Acquire::GzipIndexes "true"; Acquire::CompressionTypes::Order:: "gz";',
        "/etc/apt/apt.conf.d/02compress-indexes",
    )


def install_native_packages():
    cmd = f"apt-get update"
    sh(cmd)

    cmd = f"apt-get install -y {' '.join(PACKAGES)}"
    sh(cmd)


def install_python():
    cmd = f"python3 -m pip install {' '.join(PY_PACKAGES)}"
    sh(cmd)


def install_nodejs():
    cmd = "curl -sL https://deb.nodesource.com/setup_14.x | bash -"
    sh(cmd)
    sh("apt-get install -y nodejs")
    sh("/usr/bin/npm install -g yarn")


if __name__ == "__main__":
    main()

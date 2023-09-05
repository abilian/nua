import mmap
import os
import re
import tempfile
from collections.abc import Callable, Iterable
from glob import glob
from hashlib import sha256
from importlib import resources as rso
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import urlopen

from ..panic import Abort, info, show, warning
from ..shell import sh
from ..tool.state import verbosity
from ..unarchiver import unarchive


#
# Other stuff
#
def _glob_extended(packages: list):
    """Expand glob patterns in a list of packages."""
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


def download_extract(
    url: str,
    dest: str | Path,
    dest_name: str,
    checksum: str = "",
) -> Path:
    """Download and extract a file from a URL."""
    name = Path(url).name
    with verbosity(2):
        print("Download URL:", url)
        # info("Download URL:", url)
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / name
        download_url(url, target)
        verify_checksum(target, checksum)
        dest_path = Path(dest) / dest_name
        unarchive(target, str(dest_path))
        with verbosity(2):
            print("Project path:", dest_path)
        with verbosity(3):
            sh(f"ls -l {dest_path}")
        return dest_path


def download_url(url: str, target: Path) -> None:
    try:
        with urlopen(url) as remote:  # noqa S310
            target.write_bytes(remote.read())
    except (HTTPError, OSError):
        warning(f"download_url() failed for {url}")
        raise


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


#
# String and replacement utils
#
def set_php_ini_keys(replacements: dict, path: str | Path):
    """Set keys in a php.ini file."""
    path = Path(path)
    content = path.read_text()
    for key, value in replacements.items():
        content = re.sub(rf"^;*\s*{key}\s*=", f"{key} = {value}", content, flags=re.M)
    path.write_text(content)


def replace_in(file_pattern: str, string_pattern: str, replacement: str):
    """Replace a string in a set of files, defined by a glob pattern."""
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
    """Replace environment variables in a file."""
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


def append_bashrc(home: str | Path, content: str):
    """Append content to the bashrc file."""
    path = Path(home) / ".bashrc"
    if not path.is_file():
        raise FileNotFoundError(path)
    lines = f"# added by Nua script:\n{content}\n\n"
    with open(path, mode="a", encoding="utf8") as wfile:
        wfile.write(lines)


def snake_format(name: str) -> str:
    """Convert a string to snake_case format.
    >>> snake_format("my-project")
    'my_project'
    """
    return "_".join(word.lower() for word in name.replace("-", "_").split("_"))


def kebab_format(name: str) -> str:
    """Convert a string to kebab_case format.
    >>> kebab_format("my_project")
    'my-project'
    """
    return "-".join(word.lower() for word in name.replace("_", "-").split("-"))


def camel_format(name: str) -> str:
    """Convert a string to CamelCase format.
    >>> camel_format("my-project")
    'MyProject'
    """
    return "".join(word.title() for word in name.replace("-", "_").split("_"))


def _to_format_cases(
    formatter: Callable,
    data: dict[str, Any] | list,
    unchanged: Iterable,
    recurse: int = 999,
) -> None:
    """Converts all keys in a dict  or list to "formatter" format, with list of
    unchanged keys and recursion level, in place."""
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                _to_format_cases_dict(formatter, item, unchanged, recurse - 1)
    elif isinstance(data, dict):
        _to_format_cases_dict(formatter, data, unchanged, recurse - 1)


def _to_format_cases_dict(
    formatter: Callable,
    data: dict[str, Any],
    unchanged: Iterable,
    recurse: int = 999,
) -> None:
    """Converts all keys in a dict to "formatter" format, with list of unchanged
    keys and recursion level, in place."""
    for key, value in list(data.items()):
        if key in unchanged:
            continue
        new_key = formatter(key)
        if new_key != key:
            data[new_key] = value
            del data[key]
        if recurse > 0 and isinstance(value, (dict, list)):
            _to_format_cases(formatter, value, unchanged, recurse - 1)


def to_snake_cases(
    data: dict[str, Any],
    recurse: int = 999,
    unchanged: Iterable | None = None,
) -> None:
    """Converts all keys in a dict to snake_case, recursion level,
    in place."""
    if unchanged is None:
        unchanged = []
    _to_format_cases(snake_format, data, unchanged, recurse)


def to_kebab_cases(
    data: dict[str, Any],
    recurse: int = 999,
    unchanged: Iterable | None = None,
) -> None:
    """Converts all keys in a dict to snake_case, recursion level,
    in place."""
    if unchanged is None:
        unchanged = []
    _to_format_cases(kebab_format, data, unchanged, recurse)


def copy_from_package(
    package: str,
    filename: str,
    destdir: Path,
    destname: str = "",
):
    """Copy a file from a package to a destination directory."""
    content = rso.files(package).joinpath(filename).read_text(encoding="utf8")
    if destname:
        target = destdir / destname
    else:
        target = destdir / filename
    target.write_text(content)

import io
from collections.abc import Generator
from pathlib import Path
from tarfile import TarFile, TarInfo

import tomli
import yaml

from nua.lib.constants import NUA_METADATA_PATH, nua_config_names


class ArchiveSearch:
    """Utilities to search files in a container image stored as a .tar archive.

    Current usage: retrieve the nua-config.toml config used when
    building the Nua app.
    """

    def __init__(self, archive: str | Path) -> None:
        arch_path = Path(archive)
        if not arch_path.is_file():
            raise FileNotFoundError(arch_path)
        self.tar_file = TarFile(arch_path)
        self.equal_match = False

    #
    # Public API
    #
    def get_nua_config_dict(self) -> dict:
        """Return the nua-config.toml of the archive as a dict."""
        for name in nua_config_names():
            found = self.find_one(f"{NUA_METADATA_PATH}/{name}")
            if found:
                content = found[0]["content"]
                if name.endswith("toml"):
                    return tomli.loads(content)
                return yaml.safe_load(content)
        return {}

    #
    # Internal methods
    #
    def find_one(self, path_pattern: str) -> list:
        if path_pattern.startswith("/"):
            self.equal_match = True
        pattern = path_pattern.lstrip("/")
        if not pattern:
            raise ValueError("Empty pattern")
        return self._find_one(pattern)

    def _find_one(self, pattern: str) -> list:
        for tinfo in self.tar_file.getmembers():
            if tinfo.name.endswith(".tar"):
                result = list(self._sub_search(tinfo, pattern))
                if result:
                    return [result[0]]
        return []

    def _sub_search(self, tinfo: TarInfo, pattern: str) -> Generator:
        extracted = self.tar_file.extractfile(tinfo)
        if not isinstance(extracted, io.BufferedReader):
            raise StopIteration()
        with extracted as bytes_content:
            sub_tar = TarFile(fileobj=bytes_content)
            for sub_tinfo in sub_tar.getmembers():
                if (self.equal_match and sub_tinfo.name == pattern) or (
                    not self.equal_match and sub_tinfo.name.endswith(pattern)
                ):
                    result = {}
                    sub_extracted = sub_tar.extractfile(sub_tinfo)
                    if isinstance(sub_extracted, io.BufferedReader):
                        with sub_extracted as fileh:
                            result["content"] = fileh.read().decode("utf8")
                            result["path"] = sub_tinfo.name
                            result["member"] = tinfo.name
                        yield result

    def read(self, path: str | Path) -> str:
        """Return the content of a file on the archive."""
        result = self.find_one(str(path))
        return result[0]["content"].decode("utf8")

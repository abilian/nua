import abc
import tarfile
from pathlib import Path
from zipfile import ZipFile


class Unarchiver(abc.ABC):
    """ABC for unarchivers."""

    accepted_suffixes: list[str] = []

    @classmethod
    def accept(cls, src: str | Path) -> bool:
        src = str(src)
        for suffix in cls.accepted_suffixes:
            if src.endswith(suffix):
                return True
        return False

    @classmethod
    @abc.abstractmethod
    def extract(cls, src: str, dest_dir: str) -> None:
        raise NotImplementedError()


class TarUnarchiver(Unarchiver):
    accepted_suffixes = [".tar", ".tar.gz", ".tar.bz2", ".tar.xz", ".tgz"]

    @classmethod
    def extract(cls, src: str, dest_dir: str) -> None:
        def get_members(tar, root):
            for member in tar.getmembers():
                path = Path(member.path)
                member.path = path.relative_to(root)
                yield member

        with tarfile.open(src) as tar:
            root = Path(tar.getmembers()[0].path)
            tar.extractall(dest_dir, members=get_members(tar, root))  # noqa s202


class ZipUnarchiver(Unarchiver):
    accepted_suffixes = [".zip"]

    @classmethod
    def extract(cls, src: str, dest_dir: str) -> None:
        dest_path = Path(dest_dir)
        with ZipFile(src) as archive:
            arch_root = Path(archive.infolist()[0].filename)
            for member in archive.infolist():
                path = Path(member.filename)
                rela_path = path.relative_to(arch_root)
                target_path = dest_path.joinpath(rela_path)
                if member.is_dir():
                    target_path.mkdir(parents=True, exist_ok=True)
                    continue
                with archive.open(member) as content:
                    target_path.write_bytes(content.read())


def unarchive(src: str | Path, dest_dir: str) -> None:
    unarchivers = [TarUnarchiver, ZipUnarchiver]
    for unarchiver in unarchivers:
        if unarchiver.accept(src):
            unarchiver.extract(str(src), dest_dir)
            return
    raise ValueError(f"Unknown archive format for '{src}'")

import shutil
import tarfile
from pathlib import Path
from zipfile import ZipFile


class Unarchiver:
    """ABC for unarchivers."""

    accepted_suffixes: list[str] = []

    def accept(self, src: str | Path) -> bool:
        src = str(src)
        for suffix in self.accepted_suffixes:
            if src.endswith(suffix):
                return True
        return False

    def extract(self, src: str, dest_dir: str) -> None:
        raise NotImplementedError()


class TarUnarchiver(Unarchiver):
    accepted_suffixes = [".tar", ".tar.gz", ".tar.bz2", ".tar.xz", ".tgz"]

    def extract(self, src: str, dest_dir: str) -> None:
        def get_members(tar, root):
            for member in tar.getmembers():
                p = Path(member.path)
                member.path = p.relative_to(root)
                yield member

        with tarfile.open(src) as tar:
            root = Path(tar.getmembers()[0].path)
            tar.extractall(dest_dir, members=get_members(tar, root))


class ZipUnarchiver(Unarchiver):
    accepted_suffixes = [".zip"]

    def extract(self, src: str, dest_dir: str) -> None:
        # FIXME: doesn't set the right permissions
        with ZipFile(src) as archive:
            root = Path(archive.infolist()[0].filename)
            for member in archive.infolist():
                p = Path(member.filename)
                target_path = p.relative_to(root)
                if member.is_dir():
                    target_path.mkdir(parents=True, exist_ok=True)
                    continue
                with archive.open(member) as source, target_path.open("wb") as target:
                    shutil.copyfileobj(source, target)


def unarchive(src: str | Path, dest_dir: str) -> None:
    unarchivers = [TarUnarchiver(), ZipUnarchiver()]
    for unarchiver in unarchivers:
        if unarchiver.accept(src):
            unarchiver.extract(str(src), dest_dir)
            return
    raise ValueError(f"Unknown archive format for '{src}'")

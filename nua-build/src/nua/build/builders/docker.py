"""Docker builder (using dockerfile generated from the nua-config)."""
from __future__ import annotations
import logging
from contextlib import suppress
from importlib import resources as rso
from pathlib import Path
from shutil import copy2, copytree
import docker
from nua.lib.constants import NUA_BUILDER_TAG
from nua.lib.nua_config import hyphen_get, nua_config_names
from nua.lib.docker import (
    display_docker_img,
    docker_build_log_error,
    docker_stream_build,
)
from nua.build.autobuild.nua_image_builder import NuaImageBuilder
from nua.build.autobuild.register_builders import is_builder
from nua.lib.backports import chdir
from nua.lib.panic import debug, info, vprint
from nua.lib.shell import rm_fr
from nua.lib.tool.state import verbosity, verbosity_level

from .. import __version__
from .base import Builder, BuilderError

logging.basicConfig(level=logging.INFO)
CLIENT_TIMEOUT = 600


class DockerBuilder(Builder):
    # FIXME later
    container_type = "docker"

    def run(self):
        if not self.container_type == "docker":
            raise NotImplementedError(f"Container type '{self.container_type}'")

        self.check_allowed_base_image()
        self.ensure_base_image_profile_availability()
        self.select_base_image()
        self.title_build()
        self.detect_nua_folder()
        self.build_docker_image()
        self.post_build_notices()

    def check_allowed_base_image(self):
        builder = self.config.builder
        if not builder:
            return
        if not is_builder(builder):
            raise BuilderError(f"Unknown Nua builder: '{builder}'")

    def ensure_base_image_profile_availability(self):
        """Ensure the required Nua images are available.

        The tag 'builder' will determine the required base image if it
        represents an Image. If empty, the standard Nua base image is used.
        The builder also be an installation recipe.
        """
        image_builder = NuaImageBuilder()
        image_builder.ensure_images(self.config.builder)

    def select_base_image(self):
        """Select a base image among possible choices.

        It may append that we have 2 images for Node.js v14 and v16, and
        an app allowing both version.
        """
        builder = self.config.builder
        if builder:
            self.nua_base = NuaImageBuilder.builder_tag(builder)  # pyright: ignore
        else:
            self.nua_base = NUA_BUILDER_TAG
        with verbosity(2):
            info(f"Nua base image: '{self.nua_base}'")

    def detect_nua_folder(self):
        """Detect folder containing nua files.

        (Dockerfile, start.py, build.py, ...)
        """
        if self.config.nua_dir_exists:
            self.nua_folder = self.config.root_dir / "nua"
        else:
            self.nua_folder = self.config.root_dir
        with verbosity(3):
            debug(f"Detected Nua folder: {self.nua_folder}")

    def build_docker_image(self):
        self.copy_project_files()
        self.merge_modules_in_config()
        with verbosity(1):
            info("Write Nua config file")
        self.config.dump_json(self.build_dir)
        # copy2(self.config.path, self.build_dir)
        self.build_with_docker_stream()
        rm_fr(self.build_dir)

    def copy_project_files(self):
        """Detect and copy files to build_dir.

        - if no 'src-url', copy local source code from root_dir into build_dir
        - if 'src-url' or other remote source, do not copy local code of root_dir
        - if 'manifest' defined, copy manifest content to nua/src
        - if /nua exists, copy it to nua (but not nua/src or nua-config)
        - then copy required/default files to build_dir (nuaconfig, ...)
        """
        with verbosity(4):
            debug(f"  local build dir: {self.build_dir}")
        (self.build_dir / "nua").mkdir(mode=0o755)
        self._copy_local_code()
        self._copy_manifest_files()
        self._copy_nua_folder()
        self._copy_default_files()

    @docker_build_log_error
    def build_with_docker_stream(self):
        with chdir(self.build_dir):
            with suppress(IOError):
                copy2(
                    self.build_dir / "nua" / "Dockerfile",
                    self.build_dir,
                )
            nua_tag = self.config.nua_tag
            buildargs = {
                "nua_builder_tag": self.nua_base,
                "nua_verbosity": str(verbosity_level()),
            }
            labels = {
                "APP_ID": self.config.app_id,
                "NUA_TAG": nua_tag,
                "NUA_BUILD_VERSION": __version__,
            }

            with verbosity(0):
                info(f"Building image {nua_tag}")
            image_id = docker_stream_build(".", nua_tag, buildargs, labels)

            with verbosity(1):
                display_docker_img(nua_tag)

        if self.save_image:
            client = docker.from_env(timeout=CLIENT_TIMEOUT)
            image = client.images.get(image_id)
            self.save(image, nua_tag)  # pyright: ignore

    def _copy_local_code(self):
        if self.config.src_url or self.config.git_url:
            with verbosity(4):
                debug("  src_url or git_url -> no copy_local_code()")
            return
        with verbosity(4):
            debug("  copy_local_code()")

        # TODO: more precise filtering based on .dockerignore
        def keep(item):
            if item.name == ".dockerignore":
                return True
            return (
                not item.name.startswith(".")
                and item.name != "__pycache__"
                and item.name != "nua"
                and item.name not in set(nua_config_names())
            )

        files = [item for item in self.config.root_dir.glob("*") if keep(item)]
        with verbosity(4):
            debug(f"  copy_local_code: {(str(f) for f in (files))}")
        self._copy_items(files, self.build_dir)

    def _copy_manifest_files(self):
        if not self.config.manifest:
            return
        with verbosity(4):
            debug("  copy_manifest_files()")
        files = [self.config.root_dir / name for name in self.config.manifest]
        self._copy_items(files, self.build_dir)

    def _copy_nua_folder(self):
        if not self.config.nua_dir_exists:
            return
        with verbosity(4):
            debug("  copy_nua_folder()")
        files = [
            item
            for item in (self.config.root_dir / "nua").glob("*")
            if not item.name.startswith(".")
            and item.name not in set(nua_config_names())
        ]
        self._copy_items(files, self.build_dir / "nua")

    def _copy_items(self, paths: list[Path], dest_dir: Path):
        for path in sorted(paths):
            with verbosity(4):
                debug(f"  source path: {path}")
            if path.is_file():
                with verbosity(1):
                    info(f"Copying: {path.name}")
                copy2(path, dest_dir)
            elif path.is_dir():
                with verbosity(1):
                    info(f"Copying: {path.name}/")
                copytree(path, dest_dir / path.name, dirs_exist_ok=True)
            else:
                raise BuilderError(f"File not found: {path}")

    def _copy_default_files(self):
        """Complete missing files from defaults, at the moment the Dockerfile,
        (and maybe start.py, ...)."""
        if not hyphen_get(self.config.build, "default_files", True):
            return
        with verbosity(4):
            debug("copy_default_files()")
        for file in rso.files("nua.build.defaults").iterdir():
            if (
                not file.is_file()
                or file.name.startswith("__")
                or file.name.startswith(".")
            ):
                continue

            path = self.nua_folder / file.name
            destination = self.build_dir / "nua" / file.name
            if path.is_file():
                # file already exists, do not replace by default content, but copy
                # to /nua
                if path != destination:
                    copy2(path, self.build_dir / "nua")
                continue

            with verbosity(1):
                info("Copying Nua default file:", file.name)

            content = file.read_text(encoding="utf8")
            destination = self.build_dir / "nua" / file.name

            with verbosity(3):
                vprint(f"destination path: {destination}")

            destination.write_text(content)

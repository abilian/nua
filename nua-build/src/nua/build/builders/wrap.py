"""Docker "wrap" builder: build a container from an existing dockerfile.
"""
from __future__ import annotations

import logging

import docker
from nua.lib.docker import (
    display_docker_img,
    docker_build_log_error,
    docker_stream_build,
)
from nua.lib.backports import chdir
from nua.lib.panic import info
from nua.lib.shell import rm_fr
from nua.lib.tool.state import verbosity

from .. import __version__
from .base import Builder

logging.basicConfig(level=logging.INFO)
CLIENT_TIMEOUT = 600


class DockerWrapBuilder(Builder):
    def run(self):
        self.title_build()
        # FIXME:
        # if self.container_type != "docker":
        #     raise NotImplementedError(f"Container type '{self.container_type}'")
        self.merge_modules_in_config()
        self.write_wrap_dockerfile()
        self.build_wrap_with_docker_stream()
        rm_fr(self.build_dir)
        self.post_build_notices()

    def write_wrap_dockerfile(self):
        self.config.dump_json(self.build_dir)
        docker_file = self.build_dir / "Dockerfile"
        # if self.config.docker_user:
        #     content = (
        #         "ARG nua_wrap_tag\n"
        #         "FROM ${nua_wrap_tag}\n\n"
        #         "USER root\n"
        #         "RUN mkdir -p /nua/metadata\n"
        #         "COPY nua-config.json /nua/metadata/\n"
        #         f"USER {self.config.docker_user}\n"
        #     )
        content = (
            "ARG nua_wrap_tag\n"
            "FROM ${nua_wrap_tag}\n\n"
            "RUN mkdir -p /nua/metadata\n"
            "COPY nua-config.json /nua/metadata/\n"
        )
        docker_file.write_text(content, encoding="utf8")

    @docker_build_log_error
    def build_wrap_with_docker_stream(self):
        with chdir(self.build_dir):
            nua_tag = self.config.nua_tag
            buildargs = {
                "nua_wrap_tag": self.config.wrap_image,
            }
            labels = {
                "APP_ID": self.config.app_id,
                "NUA_TAG": nua_tag,
                "NUA_BUILD_VERSION": __version__,
            }
            info(f"Building (wrap) image {nua_tag}")
            info(f"From image {self.config.wrap_image}")
            image_id = docker_stream_build(".", nua_tag, buildargs, labels)

            with verbosity(1):
                display_docker_img(nua_tag)

        if self.save_image:
            client = docker.from_env(timeout=CLIENT_TIMEOUT)
            image = client.images.get(image_id)
            self.save(image, nua_tag)  # pyright: ignore

"""Class to manage NuaConfig format."""
from typing import Any

from pydantic import BaseModel


class Metadata(BaseModel):
    id: str
    title: str
    author: str
    description: str | None  #
    tagline: str | None  #
    website: str | None  #
    version: str  #
    release: int | None  #
    license: str = "Proprietary"  #
    src_url: str | None  #
    src_checksum: str | None  # fix
    git_url: str | None  #
    git_branch: str | None  #
    profile: str | list[str] | None  #
    tags: list[str] | None  #
    repo: str | None  # new
    base_image: str | None  #
    # Notes:
    # - src_checksum and checksum should be merged
    # name: removed, replaced by title
    # checksum: removed


class Build(BaseModel):
    method: str | None  #
    builder: str | dict | None  #
    builders: list[str] | list[dict] | None  # fix
    packages: str | list[str] | None  #
    meta_packages: str | list[str] | None  # add
    build: str | list[str] | None  # replace build command
    test: str | list[str] | None  #
    before_build: str | list[str] | None  # new
    pip_install: str | list[str] | None  # new
    project: str | None  # new

    # Deprecated
    build_command: str | list[str] | None  # add


class Run(BaseModel):
    packages: str | list[str] | None  #
    before_run: str | list[str] | None  # new
    start: str | list[str] | None  #
    # Should the '[env]' section be here or at the root ?
    # env: dict[str, Any] | None


class Port(BaseModel):
    container: str  #
    host: str | None  #
    proxy: str | None  #
    protocol: str | None  #
    ssl: str | None  #


class Healthcheck(BaseModel):
    command: str  #
    interval: int  #


class Resource(BaseModel):
    name: str
    type: str
    version: str | None
    # TODO
    backup: Any


class Volume(BaseModel):
    name: str  #
    target: str  #
    driver: str | None  #
    options: dict | None  #
    backup: Any


class NuaConfigFormat(BaseModel):
    metadata: Metadata  #
    build: Build | None  #
    run: Run | None  #
    env: dict[str, Any] | None  #
    # resources: list[Resource] | None
    resource: list[Resource] | None  #
    # volumes: list[Volume] | None
    volume: list[Volume] | None  #
    # TODO
    port: dict[str, Port] | None  #
    docker: dict | None  #
    # Should it be in `run` ?
    healthcheck: Healthcheck | None  #

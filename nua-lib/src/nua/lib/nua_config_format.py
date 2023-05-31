"""Class to manage NuaConfig format."""
from typing import Any

from pydantic import BaseModel


class Metadata(BaseModel):
    id: str
    title: str
    author: str
    description: str | None
    tagline: str | None
    website: str | None
    version: str
    release: int | None
    license: str = "Proprietary"
    src_url: str | None
    src_checksum: str | None
    git_url: str | None
    git_branch: str | None
    profile: str | list[str] | None
    tags: list[str] | None
    repo: str | None  # new
    base_image: str | None


class Build(BaseModel):
    method: str | None
    builder: str | dict | None
    builders: list[str] | list[dict] | None
    packages: str | list[str] | None
    meta_packages: str | list[str] | None
    build: str | list[str] | None
    test: str | list[str] | None
    before_build: str | list[str] | None
    pip_install: str | list[str] | None
    project: str | None

    # Obsolete, relaced by 'build':
    # build_command: str | list[str] | None  # add


class Run(BaseModel):
    packages: str | list[str] | None
    before_run: str | list[str] | None
    start: str | list[str] | None
    # Should the '[env]' section be here or at the root ?
    # env: dict[str, Any] | None


class Port(BaseModel):
    container: int | dict
    host: int | str | dict | None
    proxy: int | dict | None
    protocol: str | None
    ssl: bool | None


class Healthcheck(BaseModel):
    command: str
    interval: int
    start_period: int | None
    timeout: int | None
    retries: int | None


class Backup(BaseModel):
    method: str
    destination: str
    frequency: str
    options: dict[str, Any] | None


class Resource(BaseModel):
    name: str
    type: str
    version: str | None
    # TODO
    backup: Backup | None


class Volume(BaseModel):
    name: str | None
    target: str
    driver: str | None
    options: dict | None
    backup: Backup | None


class NuaConfigFormat(BaseModel):
    metadata: Metadata
    build: Build | None
    run: Run | None
    env: dict[str, Any] | None
    resource: list[Resource] | None  #
    volume: list[Volume] | None  #
    port: dict[str, Port] | None
    docker: dict | None
    # Should it be in `run` ?
    healthcheck: Healthcheck | None  #
from contextlib import suppress

import docker
from nua.lib.constants import NUA_BUILDER_TAG, NUA_PYTHON_TAG

from nua.build.autobuild.nua_image_builder import NuaImageBuilder

# from subprocess import run
# import shlex


def test_force_build():  # noqa
    client = docker.from_env()

    # empty docker cache
    for image in (
        NUA_BUILDER_TAG,
        NUA_PYTHON_TAG,
    ):
        with suppress(docker.errors.ImageNotFound):
            client.images.remove(image, force=True, noprune=False)
        assert not client.images.list(image)

    image_builder = NuaImageBuilder()
    image_builder.build(force=True, download=True, all=True)

    for image in (
        NUA_BUILDER_TAG,
        NUA_PYTHON_TAG,
    ):
        assert client.images.list(image)


def test_quick_build():  # noqa
    client = docker.from_env()

    image_builder = NuaImageBuilder()
    image_builder.build(all=True)

    for image in (
        NUA_BUILDER_TAG,
        NUA_PYTHON_TAG,
    ):
        assert client.images.list(image)


# def test_node_installed():  # noqa
#     cmd = f"docker run {NUA_BUILDER_NODE_TAG16} /usr/bin/node --version"
#     result = run(shlex.split(cmd), capture_output=True, text=True)
#
#     assert result.stdout.strip().startswith("v16.")

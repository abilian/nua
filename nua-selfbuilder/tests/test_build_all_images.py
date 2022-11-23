import docker
import pytest


def test_force_build():  # noqa
    from nua.selfbuilder.constants import NUA_BUILDER_TAG, NUA_PYTHON_TAG
    from nua.selfbuilder.nua_image_builder import NUAImageBuilder

    client = docker.from_env()

    # empty docker cache
    for image in (NUA_BUILDER_NODE_TAG, NUA_BUILDER_TAG, NUA_PYTHON_TAG):
        with suppress(docker.errors.ImageNotFound):
            client.images.remove(image, force=True, noprune=False)
        assert not client.images.list(image)

    image_builder = NUAImageBuilder()
    image_builder.build(force=True, download=True, all=True)

    for image in (NUA_BUILDER_NODE_TAG, NUA_BUILDER_TAG, NUA_PYTHON_TAG):
        assert client.images.list(image)

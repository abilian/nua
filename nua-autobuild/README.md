# Nua autobuild

[Nua](https://nua.rocks/) is an open source, self-hosted cloud platform project (a PaaS - platform as a service).

This packaged is mostly used internally. The main entry point is the `nua` command line tool (see: [Nua on PyPI](https://pypi.org/project/nua/) or [nua-cli on GitHub](https://github.com/abilian/nua/tree/main/nua-cli)).

This package, `nua-build`, uses base images to speed up and standardize the build of Nua packages.

If these images are not available (locally or on a remote repository), `nua-autobuild` builds them locally.

## Content

`nua-autobuild` provides:

-   `nua_image_builder`: tool to build locally the Nua standard base images
-   `nua_wheel_builder`: tool to build 'wheels' from the Nua packages
-   `docker_build_utils`: utilities to build Docker images

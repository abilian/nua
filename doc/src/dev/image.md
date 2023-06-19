# Structure of a Nua image

The structure of a Nua image is intimately linked to the image build process.

## The concept of image

A Nua image is a read-only package that contains the code needed to run an application. In practice, an image may require secondary images (called providers in Nua terminology), to perform functions delegated to other applications, for example databases.

The image concept allows fast and reproducible execution of an application with relative independence from the underlying host.

The structure of Nua images today is based on a Docker implementation, but the structure aims to allow implementations on other container technologies or other methods of isolation.

## Nua base images

### Image layers

A Docker image is made up of a series of intermediate layers, each level depending on the previous one. Layer hierarchy is the key to effective lifecycle management of the images.

-   The first levels are considered more generic and stable over time
-   Images sharing common parent images have technical consistency
-   The build (or rebuild) time of an application is minimized

### Nua base image hierarchy

Here is the image hierarchy on which the Nua image of a web application is based:

-   The current version of Nua is based on an Linux Ubuntu base image (22.04.1 LTS jammy)
-   A first image adds the Python environment (currently Python 3.10), the configuration of a 'nua' user and its Python virtual env. This image is named: **nua-python**
-   A second image based on the previous one contains the Nua agent present on all Nua application images. This image is named **nua-builder**. The Nua agent provides the features:
    -   Analysis of metadata and of the `nua-config` file (web application build guidelines, introspection of the image when it is executed by the oschestrator)
    -   Management of the application build in the image
    -   Provision of utilities for build and run scripts

### Additional Nua images

An additional image may be available to facilitate the build of an application using a particular environment.
Today Nua provides images containing the NodeJs environments version 14 and 16 (**nua-builder-nodejs14** and **nua-builder-nodejs16**).

### Availability of Nua base images

Nua base images are planned to be downloaded from an ad-hoc registry. However, the `nua-build` tool will build them locally if they are not remotely available. This is particularly the case currently in the development phase of the Nua project.
This feature is relatively transparent for the packager of an application: if the base images are not available, they are built during the build of the application (of course they are then available for subsequent builds).

## Image of the web application

### The build process and the minimal Dockerfile

Based on the above, a web app image has a `nua-builder` image as its parent image. This allows using a minimal standard Dockerfile (unless the packager explicitly provides a specific Dockerfile):

    ARG nua_builder_tag
    FROM ${nua_builder_tag}

    # app build:
    COPY . /nua/build
    ARG nua_verbosity
    RUN app_builder

    CMD ["python", "/nua/scripts/start.py"]

- During the build phase, the source code of the application is copied into the `/nua/build` folder
- The `app-builder` Nua application drives the actual build of the web app based on directives from the `nua-config` file
- Depending on the type of application, the executable code of the web app is in `/nua/build` or dispatched in `/nua/scripts` or `/nua/bin`. For Python applications, the code is installed in the virtual env of the `nua` user, in the `/nua/venv/bin` folder.

### Metadata

Application metadata is in the image's `/nua/metadata` folder. In practice it is the `nua-config` file. The orchestrator will directly read this data from the image itself. The behavior of the application is parameterized by environment variables provided by the orchestrator according to the directives of the `nua-config` file.

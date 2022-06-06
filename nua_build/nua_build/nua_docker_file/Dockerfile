FROM ubuntu:22.04
# Ubuntu 22.04 LTS with python3.10

#
# Setup base image for Nua builds
#
RUN useradd nua
RUN apt-get -y update && apt-get -y install python3.10 python3-venv python3-pip
ADD nua_build /nua/nua_build
RUN python3.10 -m venv /nua/venv
ENV VIRTUAL_ENV="/nua/venv"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN python -m pip install poetry && cd /nua/nua_build && poetry install && nuad setup_nua

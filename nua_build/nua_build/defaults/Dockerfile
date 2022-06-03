FROM ubuntu:22.04
# Ubuntu 22.04 LTS with python3.10 ?

#
# Setup base image for build & run
#
RUN useradd nua
RUN apt-get -y update && apt-get -y install curl python3.10 python3-venv python3-pip python3-setuptools python3-wheel
ADD nua_build /nua/nua_build
RUN python3.10 -m venv /nua/venv
ENV VIRTUAL_ENV="/nua/venv"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN python -m pip install poetry && cd /nua/nua_build && poetry install && nuad setup_nua

# app build:
ADD nua-config.toml /nua/build/
RUN nuad setup_app /nua/build

# debug
RUN nuad --help

#
# Configure and start
#
##ADD start.py /nua/scripts/

CMD ["/nua/scripts/start.py"]

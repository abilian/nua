FROM ubuntu:22.04
# Ubuntu 22.04 LTS with python3.10 ?

# Is this needed here ?
# ENV DEBIAN_FRONTEND noninteractive

#
# Setup base image for build & run
# TODO: split build and run
# TODO: move to base image
#
RUN useradd nua
RUN apt-get -y update && apt-get -y install curl python3.10 python3-venv python3-pip python3-setuptools python3-wheel
ADD nua_build /nua/nua_build
RUN python3.10 -m venv /nua/venv
ENV VIRTUAL_ENV="/nua/venv"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN python -m pip install poetry
RUN cd /nua/nua_build && poetry install

ADD nua-config.toml /nua/build/
##RUN python /nua/scripts/nua-setup.py
##ADD nua-build.py /nua/scripts/
##RUN python /nua/scripts/nua-build.py
RUN nuad --help

#
# Configure and start
#
##ADD start.py /nua/scripts/

CMD ["/nua/scripts/start.py"]

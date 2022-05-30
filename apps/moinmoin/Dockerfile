FROM ubuntu:20.04

# Is this needed here ?
ENV DEBIAN_FRONTEND noninteractive

#
# Setup base image for build & run
# TODO: split build and run
# TODO: move to base image
#
RUN useradd nua
RUN apt-get -y update && \
    apt-get -y install curl python3
ADD nua-setup.py /nua/scripts/
RUN python3 /nua/scripts/nua-setup.py

#
# Now install the software
#
WORKDIR /nua/build

ADD nua-build.py /nua/scripts/
ADD nua-config.toml /nua/build/
RUN python3 /nua/scripts/nua-build.py


#
# Configure and start
#
ADD start.py /nua/scripts/

CMD ["/nua/scripts/start.py"]

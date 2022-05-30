# See: https://github.com/hedgedoc/container/blob/master/debian/Dockerfile

FROM ubuntu:20.04

ARG VERSION=1.8.2

ENV DEBIAN_FRONTEND noninteractive


#
# Setup base image for build & run
# TODO: split build and run
# TODO: move to base image
#
RUN useradd nua
RUN apt-get -y update && \
    apt-get -y install curl python3
ADD setup-nua.py /app/pkg/
RUN python3 /app/pkg/setup-nua.py


#
# Now install the software
#
WORKDIR /app/code
RUN curl -sL https://github.com/hedgedoc/server/archive/${VERSION}.tar.gz \
    | tar -xz --strip-components 1 -f -
RUN yarn install --production=true --pure-lockfile


#
# Configure and start
#
ADD start.py config.json.j2 /app/pkg/

CMD ["/app/pkg/start.py"]

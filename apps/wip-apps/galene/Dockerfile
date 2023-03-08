# From: https://github.com/deburau/galene-docker/

ARG DIR=/go/src/galene
ARG VERSION=0.6.2
ARG WAIT_VERSION=2.9.0

FROM golang:alpine AS builder
ARG DIR
ARG VERSION

RUN apk --no-cache add git \
    && git clone --depth 1 --branch galene-$VERSION https://github.com/jech/galene.git ${DIR}
WORKDIR ${DIR}
RUN CGO_ENABLED=0 go build -ldflags='-s -w'

FROM alpine
ARG DIR
ARG VERSION
ARG VCS_REF=$SOURCE_COMMIT
ARG TARGET_DIR=/opt/galene
ARG WAIT_VERSION
ARG WAIT_BIN=/docker-init.d/01-docker-compose-wait

RUN mkdir -p ${TARGET_DIR}/groups/

LABEL maintainer="galene@flexoft.net"
LABEL org.label-schema.schema-version="1.0"
LABEL org.label-schema.name="galene"
LABEL org.label-schema.description="Docker image for the Galène videoconference server"
LABEL org.label-schema.url="http://galena.org/"
LABEL org.label-schema.vcs-url="https://github.com/deburau/galene"
LABEL org.label-schema.vcs-ref="${VCS_REF}"
LABEL org.label-schema.vendor="jech"
LABEL org.label-schema.version="${VERSION}"
LABEL org.label-schema.docker.cmd="docker run -it -p 8443:8443 deburau/galene:latest -turn ''"

EXPOSE 8443
EXPOSE 1194/tcp
EXPOSE 1194/udp

COPY --from=builder ${DIR}/LICENCE ${TARGET_DIR}/
COPY --from=builder ${DIR}/galene ${TARGET_DIR}/
COPY --from=builder ${DIR}/static/ ${TARGET_DIR}/static/

COPY root/ /

ADD https://github.com/ufoscout/docker-compose-wait/releases/download/${WAIT_VERSION}/wait ${WAIT_BIN}
RUN chmod 0755 ${WAIT_BIN}

WORKDIR ${TARGET_DIR}
ENTRYPOINT ["/docker-init.sh"]

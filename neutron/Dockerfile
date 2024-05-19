ARG go_version
FROM golang:${go_version} AS build

ARG neutron_version

WORKDIR /build
RUN git clone https://github.com/neutron-org/neutron && \
    cd neutron && \
    git checkout ${neutron_version} && \
    make install

WORKDIR /dist
RUN mkdir bin lib && \
    mv /go/bin/neutrond bin/

FROM ubuntu:latest

COPY --from=build /dist/bin/* /usr/local/bin/

COPY entrypoint.sh /usr/local/bin/

RUN chmod +x /usr/local/bin/*

ENTRYPOINT ["entrypoint.sh"]
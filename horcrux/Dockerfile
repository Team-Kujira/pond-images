ARG go_version
FROM golang:${go_version} AS build

ARG horcrux_version

WORKDIR /build
RUN git clone https://github.com/strangelove-ventures/horcrux.git && \
    cd horcrux && \
    git checkout ${horcrux_version} && \
    make install

WORKDIR /dist
RUN mkdir bin lib && \
    mv /go/bin/horcrux bin/

FROM ubuntu:latest
RUN userdel ubuntu

COPY --from=build /dist/bin/* /usr/local/bin/

COPY entrypoint.sh /usr/local/bin/

RUN chmod +x /usr/local/bin/*

ENTRYPOINT ["entrypoint.sh"]
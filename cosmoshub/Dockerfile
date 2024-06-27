ARG go_version
FROM golang:${go_version} AS build

ARG cosmoshub_version

WORKDIR /build
RUN git clone https://github.com/cosmos/gaia && \
    cd gaia && \
    git checkout ${cosmoshub_version} && \
    make install

WORKDIR /dist
RUN mkdir bin lib && \
    mv $(ldd /go/bin/gaiad | egrep "libwasmvm.[^\.]+.so" | awk '{print $3}') lib/ && \
    mv /go/bin/gaiad bin/

FROM ubuntu:latest
RUN userdel ubuntu

COPY --from=build /dist/bin/* /usr/local/bin/
COPY --from=build /dist/lib/* /usr/lib/

COPY entrypoint.sh /usr/local/bin/

RUN chmod +x /usr/local/bin/*

ENTRYPOINT ["entrypoint.sh"]
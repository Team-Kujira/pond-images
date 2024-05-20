ARG go_version
FROM golang:${go_version} AS build

ARG terra2_version

WORKDIR /build
RUN git clone https://github.com/terra-money/core && \
    cd core && \
    git checkout ${terra2_version} && \
    make install

WORKDIR /dist
RUN mkdir bin lib && \
    mv $(ldd /go/bin/terrad | egrep "libwasmvm.[^\.]+.so" | awk '{print $3}') lib/ && \
    mv /go/bin/terrad bin/

FROM ubuntu:latest

COPY --from=build /dist/bin/* /usr/local/bin/
COPY --from=build /dist/lib/* /usr/lib/

RUN chmod +x /usr/local/bin/*

ENTRYPOINT ["entrypoint.sh"]
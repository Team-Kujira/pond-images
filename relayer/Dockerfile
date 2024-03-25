ARG go_version
FROM golang:${go_version} AS build

ARG relayer_version

WORKDIR /build
RUN git clone https://github.com/cosmos/relayer.git && \
    cd relayer && \
    git checkout ${relayer_version} && \
    make install

WORKDIR /dist
RUN mkdir bin && \
    mv /go/bin/rly bin/

FROM ubuntu:latest

COPY --from=build /dist/bin/* /usr/local/bin/

COPY entrypoint.sh link-and-start.sh /usr/local/bin/

RUN chmod +x /usr/local/bin/*

ENTRYPOINT ["entrypoint.sh"]
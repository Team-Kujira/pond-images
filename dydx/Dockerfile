ARG go_version
FROM golang:${go_version} AS build

ARG dydx_version

WORKDIR /build
RUN git clone https://github.com/dydxprotocol/v4-chain.git && \
    cd v4-chain/protocol && \
    git checkout protocol/${dydx_version} && \
    make install

WORKDIR /dist
RUN mkdir bin lib && \
    mv /go/bin/dydxprotocold bin/
# mv $(ldd /go/bin/dydxprotocold | egrep "libwasmvm.[^\.]+.so" | awk '{print $3}') lib/ && \


FROM ubuntu:latest
RUN userdel ubuntu

COPY --from=build /dist/bin/* /usr/local/bin/
# COPY --from=build /dist/lib/* /usr/lib/

COPY entrypoint.sh /usr/local/bin/

RUN chmod +x /usr/local/bin/*

ENTRYPOINT ["entrypoint.sh"]
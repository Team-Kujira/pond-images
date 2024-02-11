ARG go_version
FROM golang:${go_version} AS build

ARG kujira_version

WORKDIR /build
RUN git clone --depth 1 --branch ${kujira_version} https://github.com/Team-Kujira/core.git && \
    cd core && \
    make install

WORKDIR /dist
RUN mkdir bin lib && \
    mv $(ldd /go/bin/kujirad | egrep "libwasmvm.[^\.]+.so" | awk '{print $3}') lib/ && \
    mv /go/bin/kujirad bin/

FROM ubuntu:latest

COPY --from=build /dist/bin/* /usr/local/bin/
COPY --from=build /dist/lib/* /usr/lib/

COPY entrypoint.sh /usr/local/bin/

RUN chmod +x /usr/local/bin/*

ENTRYPOINT ["entrypoint.sh"]
ARG go_version
FROM golang:${go_version} AS build

ARG feeder_version

WORKDIR /build
RUN git clone --depth 1 --branch ${feeder_version} https://github.com/Team-Kujira/oracle-price-feeder.git && \
    cd oracle-price-feeder && \
    make install

WORKDIR /dist
RUN mkdir bin && \
    mv /go/bin/price-feeder bin/

FROM ubuntu:latest
RUN userdel ubuntu

RUN apt-get update && apt-get install --yes ca-certificates

COPY --from=build /dist/bin/* /usr/local/bin/

COPY entrypoint.sh /usr/local/bin/

RUN chmod +x /usr/local/bin/entrypoint.sh

WORKDIR /feeder

ENTRYPOINT ["entrypoint.sh"]

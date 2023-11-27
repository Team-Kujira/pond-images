ARG namespace
ARG feeder_version
ARG arch
FROM ${namespace}/feeder:${feeder_version}-${arch}

ARG feeder_version
ENV VERSION=${feeder_version}

RUN echo "$VERSION"

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-jinja2 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY prepare.py entrypoint.sh /usr/local/bin/
COPY templates /tmp/templates

RUN chmod +x /usr/local/bin/*

WORKDIR /tmp

ENTRYPOINT ["entrypoint.sh"]


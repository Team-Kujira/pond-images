ARG namespace
ARG kujira_version
ARG arch
FROM ${namespace}/kujira:${kujira_version}-${arch}

ARG kujira_version
ARG feeder_version
ARG relayer_version
ENV KUJIRA_VERSION=${kujira_version}
ENV FEEDER_VERSION=${feeder_version}
ENV RELAYER_VERSION=${relayer_version}

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-jinja2 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY prepare.py entrypoint.sh /usr/local/bin/
COPY templates /tmp/templates
COPY keys /tmp/keys
COPY mnemonics.json /tmp/mnemonics.json

RUN chmod +x /usr/local/bin/*

WORKDIR /tmp

ENTRYPOINT ["entrypoint.sh"]


ARG namespace
ARG kujira_version
ARG arch
FROM ${namespace}/kujira:${kujira_version}-${arch}

WORKDIR /tmp
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ca-certificates \
    python3 \
    python3-jinja2 \
    python3-mako \
    python3-requests \
    python3-yaml \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY prepare.py entrypoint.sh /usr/local/bin/
COPY templates /tmp/templates
COPY keys /tmp/keys
COPY mnemonics.json /tmp/mnemonics.json
COPY contracts /tmp/contracts

RUN chmod +x /usr/local/bin/*

ARG kujira_version
ARG feeder_version
ARG relayer_version
ARG prepare_version
ENV KUJIRA_VERSION=${kujira_version}
ENV FEEDER_VERSION=${feeder_version}
ENV RELAYER_VERSION=${relayer_version}
ENV PREPARE_VERSION=${prepare_version}

WORKDIR /tmp

ENTRYPOINT ["entrypoint.sh"]


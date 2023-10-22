ARG kujira_version
FROM teamkujira/kujirad:${kujira_version}

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY contracts.py /usr/local/bin/

RUN chmod +x /usr/local/bin/*

WORKDIR /tmp

ENTRYPOINT ["contracts.py"]


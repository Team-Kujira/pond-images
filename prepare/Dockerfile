ARG kujira_version
ARG arch
FROM teamkujira/kujirad:${kujira_version}-${arch}

RUN apt-get update && apt-get install --yes python3 python3-jinja2

COPY prepare.py /usr/local/bin/
COPY entrypoint.sh /usr/local/bin/
COPY templates /tmp/templates

RUN chmod +x /usr/local/bin/*

WORKDIR /tmp

ENTRYPOINT ["entrypoint.sh"]


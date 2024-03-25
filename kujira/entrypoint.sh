#!/bin/bash

if [ -n "$USER" ]; then
    useradd -u $USER kujira -d /tmp/kujira
    chown -R kujira /kujira

    exec runuser -u kujira -- "$@"
else
    $@
fi

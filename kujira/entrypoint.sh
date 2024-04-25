#!/bin/bash

if [ -n "$USER" ]; then
    useradd -u $USER kujira
    chown -R kujira /home/kujira

    exec runuser -u kujira -- $@
else
    $@
fi

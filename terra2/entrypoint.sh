#!/bin/bash

if [ -n "$USER" ]; then
    useradd -u $USER terra2
    chown -R terra2 /home/terra2

    exec runuser -u terra2 -- $@
else
    $@
fi

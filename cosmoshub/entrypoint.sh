#!/bin/bash

if [ -n "$USER" ]; then
    useradd -u $USER cosmos -d /tmp/cosmoshub
    chown -R cosmoshub /cosmoshub

    exec runuser -u cosmoshub -- "$@"
else
    $@
fi

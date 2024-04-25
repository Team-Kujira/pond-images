#!/bin/bash

if [ -n "$USER" ]; then
    useradd -u $USER relayer
    chown -R relayer /home/relayer

    exec runuser -u relayer -- $@
else
    $@
fi

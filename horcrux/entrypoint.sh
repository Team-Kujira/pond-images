#!/bin/bash

if [ -n "$USER" ]; then
    useradd -u $USER horcrux
    chown -R horcrux /home/horcrux

    exec runuser -u horcrux -- $@
else
    $@
fi

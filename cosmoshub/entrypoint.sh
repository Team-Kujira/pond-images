#!/bin/bash

if [ -n "$USER" ]; then
    useradd -u $USER cosmoshub
    chown -R cosmoshub /home/cosmoshub

    exec runuser -u cosmoshub -- $@
else
    $@
fi

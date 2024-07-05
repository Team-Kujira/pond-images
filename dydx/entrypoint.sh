#!/bin/bash

if [ -n "$USER" ]; then
    useradd -u $USER dydx
    chown -R dydx /home/dydx

    exec runuser -u dydx -- $@
else
    $@
fi

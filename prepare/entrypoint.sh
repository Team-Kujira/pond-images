#!/bin/bash

if [ -n "$USER" ]; then
    useradd -u $USER prepare
    chown -R prepare /tmp/pond

    exec runuser -u prepare -- "$@"
else
    $@
fi
#!/bin/bash

if [ -n "$USER" ]; then
    useradd -u $USER -md /feeder feeder
    chown -R feeder /feeder

    exec runuser -u feeder -- "$@"
else
    $@
fi

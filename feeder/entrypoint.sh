#!/bin/bash

if [ -n "$USER" ]; then
    useradd -u $USER feeder
    chown -R feeder /home/feeder

    exec runuser -u feeder -- $@
else
    $@
fi

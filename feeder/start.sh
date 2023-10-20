#!/bin/bash

if [ -n "$USER" ]; then
    useradd -u $USER -m feeder
    chown -R feeder /feeder

    cd /feeder
    exec runuser -u feeder -- echo "" | price-feeder config.toml
else
    cd /feeder
    echo "" | price-feeder config.toml
fi

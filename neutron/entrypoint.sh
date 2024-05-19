#!/bin/bash

if [ -n "$USER" ]; then
    useradd -u $USER neutron
    chown -R neutron /home/neutron

    exec runuser -u neutron -- $@
else
    $@
fi

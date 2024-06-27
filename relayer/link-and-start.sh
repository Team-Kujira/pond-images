#!/bin/bash

for path in $@; do
    rly --home /home/relayer paths show $path -j | grep -q '"connection":false' && \
    rly --home /home/relayer tx link $path
done

rly --home /home/relayer start
#!/bin/bash

for path in $@; do
    rly --home /relayer paths show $path -j | grep -q '"connection":false' && \
    rly --home /relayer tx link $path
done

rly --home /relayer start
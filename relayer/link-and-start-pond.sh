#!/bin/bash

rly --home /relayer paths show pond -j | grep -q '"connection":false' && \
rly --home /relayer tx link pond

rly --home /relayer start
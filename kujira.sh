#!/bin/bash

if [ "$1" == "tx" ]; then
  extra="--from validator --keyring-backend test  --gas auto --gas-adjustment 2"
fi

kujirad-v0.8.8-43-gc5a82f3 \
    --node http://localhost:10157 $@ \
    --home /tmp/pond --chain-id pond-1 $extra

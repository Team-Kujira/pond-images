#!/bin/bash

action=build
if [ $# -eq 1 ] && [ "$1" == "manifest" ]; then
    action=manifest
fi

if [ -n "$(which docker)" ]; then
    cmd=docker
elif [ -n "$(which podman)" ]; then
    cmd=podman
else
    exit 1
fi

cmd=podman

arch=$(arch)

# contracts
kujira_version=v0.9.0
tag=starsquid/contracts:${kujira_version}

if [ "$action" == "build" ]; then
    $cmd build \
        --tag ${tag}-${arch} \
        --build-arg kujira_version=${kujira_version} \
        contracts 

    # $cmd push $tag-${arch}
fi

if [ "$action" == "manifest" ]; then
    $cmd manifest create ${tag} ${tag}-x86_64 ${tag}-arm64
    $cmd manifest push ${tag}
fi

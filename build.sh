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

arch=$(arch)

# kujirad
go_version=1.20.2
kujira_version=v0.9.0
tag=teamkujira/kujirad:${kujira_version}

if [ "$action" == "build" ]; then
    $cmd build \
        --tag ${tag}-${arch} \
        --build-arg go_version=${go_version} \
        --build-arg kujira_version=${kujira_version} \
        kujirad && \

    $cmd push $tag-${arch}
fi

if [ "$action" == "manifest" ]; then
    $cmd manifest create ${tag} ${tag}-x86_64 ${tag}-arm64
    $cmd manifest push ${tag}
fi

# feeder
go_version=1.20.2
feeder_version=next
tag=teamkujira/feeder:${feeder_version}

if [ "$action" == "build" ]; then
    $cmd build \
        --tag ${tag}-${arch} \
        --build-arg go_version=${go_version} \
        --build-arg feeder_version=${feeder_version} \
        feeder && \
    
    $cmd push $tag-${arch}   
fi


if [ "$action" == "manifest" ]; then
    $cmd manifest create ${tag} ${tag}-x86_64 ${tag}-arm64
    $cmd manifest push ${tag}
fi

# prepare
prepare_version=latest
tag=teamkujira/prepare:${prepare_version}

if [ "$action" == "build" ]; then
    $cmd build \
        --tag ${tag}-${arch} \
        --build-arg kujira_version=${kujira_version} \
        --build-arg arch=${arch} \
        prepare && \

    $cmd push $tag-${arch}
fi

if [ "$action" == "manifest" ]; then
    $cmd manifest create ${tag} ${tag}-x86_64 ${tag}-arm64
    $cmd manifest push ${tag}
fi
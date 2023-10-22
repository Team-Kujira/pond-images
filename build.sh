#!/bin/bash

cmd=""
action=build
namespace="teamkujira"
if [ $# -gt 0 ]; then
    if [ "$1" == "manifest" ]; then
        action=manifest
    fi

    if [ "$1" == "docker" ] || [ "$1" == "podman" ]; then
        cmd="$1"
    fi

    if [ $# -eq 2 ]; then
        namespace=$2
    fi
fi

if [ -z "$cmd" ]; then
    if [ -n "$(which docker)" ]; then
        cmd=docker
    elif [ -n "$(which podman)" ]; then
        cmd=podman
    else
        exit 1
    fi
fi

arch=$(arch)

# kujirad
go_version=1.20.2
kujira_version=v0.9.0
tag=${namespace}/kujirad:${kujira_version}

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
tag=${namespace}/feeder:${feeder_version}

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
tag=${namespace}/prepare:${prepare_version}

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
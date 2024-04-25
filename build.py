#!/usr/bin/env python3

import argparse
import platform
import subprocess
import sys
import yaml
import datetime as dt


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--namespace", default="teamkujira")
    parser.add_argument("-a", "--app")
    parser.add_argument("-t", "--tag")
    parser.add_argument("--push", action="store_true")
    parser.add_argument("--podman", action="store_true")
    parser.add_argument("--manifest", action="store_true")
    parser.add_argument("--archs")
    return parser.parse_args()


def build_arg(s):
    return ["--build-arg", s]


def get_version(versions, name, tag):
    versions = versions["pond"]
    version = versions.get(tag, {}).get(name)
    if not version:
        version = versions["latest"].get(name)

    if not version:
        raise f"no version found for {name}"

    return version


def build(command, namespace, app, tag, versions, push=False):
    arch = platform.machine()

    if arch == "x86_64":
        arch = "amd64"

    fulltag = f"{namespace}/{app}:{tag}-{arch}"

    cmd = [command, "build", "--tag", fulltag]

    go_version = versions["go"].get(app, {}).get(tag)
    if not go_version and app != "proxy":
        print(f"no go version defined for {app}:{tag}")
        sys.exit(1)

    cmd += build_arg(f"{app}_version={tag}")
    if go_version:
        cmd += build_arg(f"go_version={go_version}")

    cmd.append(app)

    print(" ".join(cmd))
    subprocess.run(cmd)

    push_cmds = [
        [command, "push", fulltag]
    ]

    print(push_cmds)

    if push:
        for cmd in push_cmds:
            print(cmd)
            subprocess.run(cmd)


def manifest(command, namespace, app, tag, archs, push=False):
    fulltag = f"{namespace}/{app}:{tag}"
    commands = []

    tags = [f"{fulltag}-{x}" for x in archs.split(",")]
    commands.append([command, "manifest", "create", fulltag] + tags)

    if push:
        if command == "podman":
            commands.append([command, "manifest", "push", fulltag, fulltag])
        else:
            commands.append([command, "manifest", "push", fulltag])

    for cmd in commands:
        print(cmd)
        subprocess.run(cmd)


def main():
    args = parse_args()

    versions = yaml.safe_load(open("versions.yml", "r"))

    pond_version = args.tag
    if not pond_version:
        pond_version = dt.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        versions["pond"][pond_version] = versions["pond"]["latest"]

    command = "docker"
    if args.podman:
        command = "podman"

    apps = ["kujira", "feeder", "relayer", "proxy", "terra2", "cosmoshub"]
    if args.app:
        apps = [args.app]

    for app in apps:
        tag = versions["pond"][pond_version].get(app)

        if not tag:
            print(f"no tag defined for {app} ({pond_version})")
            sys.exit(1)

        build(command, args.namespace, app, tag, versions, args.push)

        if not args.manifest:
            continue

        archs = args.archs
        if not archs:
            archs = platform.machine()

            if archs == "x86_64":
                archs = "amd64"

        manifest(command, args.namespace, app, tag, archs, args.push)


if __name__ == "__main__":
    main()

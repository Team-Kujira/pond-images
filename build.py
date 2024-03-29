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

    if app in ["feeder", "kujira", "relayer"]:
        go_version = versions["go"].get(app, {}).get(tag)
        if not go_version:
            print(f"no go version defined for {app}:{tag}")
            sys.exit(1)

        cmd += build_arg(f"{app}_version={tag}")
        cmd += build_arg(f"go_version={go_version}")

    if app == "prepare":
        kujira_version = get_version(versions, "kujira", tag)
        feeder_version = get_version(versions, "feeder", tag)
        relayer_version = get_version(versions, "relayer", tag)

        cmd += build_arg(f"kujira_version={kujira_version}")
        cmd += build_arg(f"feeder_version={feeder_version}")
        cmd += build_arg(f"relayer_version={relayer_version}")
        cmd += build_arg(f"prepare_version={tag}")
        cmd += build_arg(f"namespace={namespace}")
        cmd += build_arg(f"arch={arch}")

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
    commands.append([command, "manifest", "create", f"{fulltag}"] + tags)

    if push:
        commands.append([command, "manifest", "push", f"{fulltag}"])

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

    apps = ["kujira", "feeder", "relayer", "prepare"]
    if args.app:
        apps = [args.app]

    for app in apps:
        tag = versions["pond"][pond_version].get(app)
        if app == "prepare":
            tag = pond_version

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

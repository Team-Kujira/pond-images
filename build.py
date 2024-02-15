#!/usr/bin/env python3

import argparse
import platform
import subprocess
import sys
import yaml


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--namespace", default="teamkujira")
    parser.add_argument("-a", "--app")
    parser.add_argument("-t", "--tag", required=True)
    parser.add_argument("--push", action="store_true")
    parser.add_argument("--podman", action="store_true")
    parser.add_argument("--manifest", action="store_true")
    parser.add_argument("--archs")
    return parser.parse_args()


def build_arg(s):
    return ["--build-arg", s]


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
        kujira_version = versions["pond"][tag]["kujira"]
        feeder_version = versions["pond"][tag]["feeder"]
        relayer_version = versions["pond"][tag]["relayer"]

        cmd += build_arg(f"kujira_version={kujira_version}")
        cmd += build_arg(f"feeder_version={feeder_version}")
        cmd += build_arg(f"relayer_version={relayer_version}")
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

    print("------------------")
    print(fulltag)

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

    command = "docker"
    if args.podman:
        command = "podman"

    apps = ["kujira", "feeder", "relayer", "prepare"]
    if args.app:
        apps = [args.app]

    for app in apps:
        tag = versions["pond"][args.tag].get(app)
        if app == "prepare":
            tag = args.tag

        if not tag:
            print(f"no tag defined for {app} ({args.tag})")
            sys.exit(1)

        build(command, args.namespace, app, tag, versions, args.push)

        if not args.manifest:
            return

        if not args.archs:
            archs = platform.machine()

            if archs == "x86_64":
                archs = "amd64"

        manifest(command, args.namespace, app, tag, archs, args.push)


if __name__ == "__main__":
    main()

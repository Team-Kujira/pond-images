#!/usr/bin/env python3

import argparse
import platform
import subprocess
import sys

GO_VERSIONS = {
    "kujira": {
        "v0.9.0":  "1.20.2",
        "v0.9.1":  "1.20.2",
        "v0.9.2":  "1.20.2",
        "v0.9.3-1":  "1.20.2",
        "sdk-50":  "1.21.3",
    },
    "feeder": {
        "v0.8.3": "1.20.2",
        "v0.11.0": "1.20.2",
    },
    "relayer": {
        "v2.5.0": "1.21.7",
    }
}

VERSIONS = {
    "v0.1.0": {
        "kujira": "v0.9.3-1",
        "feeder": "v0.11.0",
        "relayer": "v2.5.0"
    }
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--namespace", default="teamkujira")
    parser.add_argument("-a", "--app")
    parser.add_argument("-t", "--tag", default="v0.1.0")
    parser.add_argument("--push", action="store_true")
    parser.add_argument("--podman", action="store_true")
    parser.add_argument("--manifest", action="store_true")
    parser.add_argument("--archs", default=platform.machine())
    return parser.parse_args()


def build_arg(s):
    return ["--build-arg", s]


def build(command, namespace, app, tag, push=False):
    arch = platform.machine()
    fulltag = f"{namespace}/{app}:{tag}-{arch}"

    cmd = [command, "build", "--tag", fulltag]

    if app in ["feeder", "kujira", "relayer"]:
        go_version = GO_VERSIONS.get(app, {}).get(tag)
        if not go_version:
            print(f"no go version defined for {app}:{tag}")
            sys.exit(1)

        cmd += build_arg(f"{app}_version={tag}")
        cmd += build_arg(f"go_version={go_version}")

    if app == "prepare":
        kujira_version = VERSIONS[tag]["kujira"]
        feeder_version = VERSIONS[tag]["feeder"]
        relayer_version = VERSIONS[tag]["relayer"]

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

    command = "docker"
    if args.podman:
        command = "podman"

    apps = ["kujira", "feeder", "relayer", "prepare"]
    if args.app:
        apps = [args.app]

    for app in apps:
        tag = VERSIONS[args.tag].get(app)
        if app == "prepare":
            tag = args.tag

        if not tag:
            print(f"no tag defined for {app} ({args.tag})")
            sys.exit(1)

        build(command, args.namespace, app, tag, args.push)

        if not args.manifest:
            return

        manifest(command, args.namespace, app, tag, args.archs, args.push)


if __name__ == "__main__":
    main()

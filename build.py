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
        "sdk-50":  "1.21.3",
    },
    "feeder": {
        "v0.8.3": "1.20.2",
    }
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["build", "manifest"])
    parser.add_argument("-n", "--namespace", default="teamkujira")
    parser.add_argument("-a", "--app", required=True)
    parser.add_argument("-t", "--tag", required=True)
    parser.add_argument("--push", action="store_true")
    parser.add_argument("--podman", action="store_true")
    parser.add_argument("--mainnet", action="store_true")
    parser.add_argument("--testnet", action="store_true")
    return parser.parse_args()


def build(command, namespace, app, tag, push=False, extra_tags=[]):
    arch = platform.machine()
    fulltag = f"{namespace}/{app}:{tag}-{arch}"
    baseapp = app.replace("prepare-", "")

    cmd = [command, "build", "--tag", fulltag]

    if baseapp in ["feeder", "kujira"]:
        go_version = GO_VERSIONS.get(baseapp, {}).get(tag)
        if not go_version:
            print(f"no go version defined for {baseapp}:{tag}")
            sys.exit(1)

        cmd += ["--build-arg", f"{baseapp}_version={tag}"]
        cmd += ["--build-arg", f"go_version={go_version}"]

    if app.startswith("prepare-"):
        cmd += ["--build-arg", f"namespace={namespace}"]
        cmd += ["--build-arg", f"arch={arch}"]

    cmd.append(app)

    print(" ".join(cmd))
    subprocess.run(cmd)

    push_cmds = [
        [command, "push", fulltag]
    ]

    for tag in extra_tags:
        print(tag)
        newtag = f"{namespace}/{app}:{tag}-{arch}"
        subprocess.run([command, "tag", fulltag, newtag])
        push_cmds.append([command, "push", newtag])

    print(push_cmds)

    if push:
        for cmd in push_cmds:
            print(cmd)
            subprocess.run(cmd)


def manifest(command, namespace, app, tag, push=False, extra_tags=[]):
    push_commands = []
    basetag = f"{namespace}/{app}"

    fulltag = f"{basetag}:{tag}"
    print("------------------")
    print(fulltag)
    subprocess.run([
        command, "manifest", "create", f"{fulltag}",
        f"{fulltag}-arm64", f"{fulltag}-x86_64"
    ])

    push_commands.append(
        [command, "manifest", "push", f"{fulltag}"]
    )

    for tag in extra_tags:
        print(tag)
        newtag = f"{basetag}:{tag}"
        subprocess.run([command, "tag", fulltag, newtag])
        push_commands.append([command, "push", newtag])

    if push:
        for cmd in push_commands:
            print(cmd)
            subprocess.run(cmd)


def main():
    args = parse_args()

    command = "docker"
    if args.podman:
        command = "podman"

    apps = [args.app]
    if args.app in ["feeder", "kujira"]:
        apps.append(f"prepare-{args.app}")

    print(apps)

    for app in apps:
        extra_tags = []
        if args.testnet:
            extra_tags.append("testnet")
        if args.mainnet:
            extra_tags.append("mainnet")

        if args.action == "build":

            build(command, args.namespace, app,
                  args.tag, args.push, extra_tags)
        elif args.action == "manifest":
            manifest(command, args.namespace, app,
                     args.tag, args.push, extra_tags)


if __name__ == "__main__":
    main()

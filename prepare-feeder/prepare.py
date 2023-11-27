#!/usr/bin/env python3

import json
import os
import jinja2
import argparse
import sys

WORKDIR = "pond"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--podman", action="store_true",
                        help="Generate start/stop scripts for podman")

    return parser.parse_args()


def main():
    args = parse_args()

    if not os.path.isdir(WORKDIR):
        sys.exit(1)

    config = {
        "command": "docker",
        "chains": {}
    }

    if args.podman:
        config["command"] = "podman"

    config = json.load(open(f"{WORKDIR}/pond.json", "r"))

    chains = config.get("chains", {})
    chain = chains.get("pond-1")
    if not chain:
        print(f"chain 'pond-1' not found")
        sys.exit(1)

    feeder_toml = jinja2.Template(
        open("templates/config.toml.j2", "r").read()
    )

    for validator in chain["validators"]:
        port_prefix = validator["rpc_url"][-5:-2]
        params = {
            "grpc_port": f"{port_prefix}{90}",
            "rpc_port": f"{port_prefix}{57}",
            "feeder_port": f"{port_prefix}{71}",
            "moniker": validator["moniker"],
            "address": validator["address"],
            "valoper": validator["valoper"],
            "chain_id": "pond-1",
            "podman": args.podman
        }

        name = validator["moniker"].lower().replace("kujira", "feeder")
        home = f"{WORKDIR}/{name}"
        if os.path.isdir(home):
            continue

        os.mkdir(home)

        open(f"{home}/config.toml", "w").write(
            feeder_toml.render(params)
        )

    # update version
    version = config.get("version", {})
    version["feeder"] = os.environ.get("VERSION")
    config["version"] = version

    json.dump(config, open(f"{WORKDIR}/pond.json", "w"))


if __name__ == "__main__":
    main()

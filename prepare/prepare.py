#!/usr/bin/env python3

import json
import shutil
import subprocess
import os
import jinja2
import argparse

WORKDIR = "pond"


class Chain:
    name = ""
    denom = "stake"
    chain_id = ""
    validators = []
    port_prefix = 1
    podman = False
    rpc_port = ""

    def __init__(self, name, chain_id, denom, num_validators, port_prefix, podman):
        self.name = name
        self.chain_id = chain_id
        self.denom = denom
        self.port_prefix = port_prefix
        self.podman = podman

        gentxs = []
        self.validators = []

        for i in range(1, num_validators + 1):
            home = f"{WORKDIR}/{name.lower()}{i:02}"

            if os.path.isdir(home):
                continue

            os.mkdir(home)

            info, gentx = self.prepare_gentxs(chain_id, home)
            info["rpc_port"] = f"{self.port_prefix}{i:02}57"
            info["api_port"] = f"{self.port_prefix}{i:02}17"
            self.validators.append(info)

            gentxs.append(gentx)

        self.prepare_genesis(gentxs)
        self.prepare_config()

    def prepare_gentxs(self, chain_id, home, amount=10**15):
        moniker = home.split("/")[-1].title()
        denom = self.denom

        kujirad = ["kujirad", "--home", home]

        result = subprocess.run(kujirad + [
            "init", moniker, "--chain-id", chain_id,
            "--default-denom", self.denom
        ], capture_output=True, text=True)

        output = json.loads(result.stderr)
        node_id = output["node_id"]

        kujirad += ["--output", "json"]

        result = subprocess.run(kujirad + [
            "keys", "add", "validator", "--keyring-backend", "test",
        ], capture_output=True, text=True)

        output = json.loads(result.stdout)
        address = output["address"]
        mnemonic = output["mnemonic"]

        subprocess.run(kujirad + [
            "genesis", "add-genesis-account", address, f"{amount}{denom}"
        ])

        staked = amount / 2
        result = subprocess.run(kujirad + [
            "genesis", "gentx", "validator", f"{staked}{denom}",
            "--chain-id", chain_id, "--keyring-backend", "test"
        ], capture_output=True, text=True)

        gentx_path = f"{home}/config/gentx"
        gentx_file = os.listdir(gentx_path)[0]
        gentx_data = json.load(open(f"{gentx_path}/{gentx_file}", "r"))

        info = {
            "moniker": moniker,
            "address": address,
            "valoper": gentx_data["body"]["messages"][0]["validator_address"],
            "node_id": node_id,
            "mnemonic": mnemonic,
            "amount": amount
        }

        return info, gentx_data

    def prepare_genesis(self, gentxs):
        name = self.name.lower()
        home = f"{WORKDIR}/{name}01"

        kujirad = ["kujirad", "--home", home]

        for i in range(1, len(self.validators)):
            info = self.validators[i]
            address = info["address"]
            amount = info["amount"]
            subprocess.run(kujirad + [
                "genesis", "add-genesis-account", address, f"{amount}{self.denom}"
            ])

            json.dump(
                gentxs[i],
                open(f"{home}/config/gentx/gentx-{info['node_id']}.json", "w")
            )

        subprocess.run(kujirad + [
            "genesis", "collect-gentxs"
        ])

        genesis = json.load(open(f"{home}/config/genesis.json"))

        genesis["app_state"]["crisis"]["constant_fee"]["denom"] = self.denom
        genesis["app_state"]["denom"]["params"]["creation_fee"][0]["denom"] = self.denom
        genesis["app_state"]["gov"]["params"]["min_deposit"][0]["denom"] = self.denom
        genesis["app_state"]["gov"]["params"]["max_deposit_period"] = "20s"
        genesis["app_state"]["gov"]["params"]["voting_period"] = "20s"
        genesis["app_state"]["mint"]["minter"]["inflation"] = "0"
        genesis["app_state"]["mint"]["params"]["mint_denom"] = self.denom
        if self.denom == "ukuji":
            genesis["app_state"]["oracle"]["params"]["whitelist"] = [
                {"name": "BTC"},
                {"name": "ETH"}
            ]
        genesis["app_state"]["staking"]["params"]["unbonding_time"] = "120s"
        genesis["app_state"]["staking"]["params"]["bond_denom"] = self.denom

        for i in range(len(self.validators)):
            json.dump(
                genesis,
                open(f"{WORKDIR}/{name}{i+1:02}/config/genesis.json", "w"),
            )

    def prepare_config(self):
        app_toml = jinja2.Template(
            open("templates/app.toml.j2", "r").read()
        )
        config_toml = jinja2.Template(
            open("templates/config.toml.j2", "r").read()
        )
        feeder_toml = jinja2.Template(
            open("templates/feeder.toml.j2", "r").read()
        )

        for index, info in enumerate(self.validators):
            num = f"{index+1:02}"
            home = f"{WORKDIR}/{self.name.lower()}{num}"

            node_id = info["node_id"]

            persistent_peers = []
            for i, v in enumerate(self.validators):
                if v["node_id"] == node_id:
                    continue
                port = f"{self.port_prefix}{i+1:02}{56}"
                host = v["moniker"].lower()
                if self.podman:
                    host = "127.0.0.1"
                persistent_peers.append(f"{v['node_id']}@{host}:{port}")

            config = {
                "api_port": f"{self.port_prefix}{num}{17}",
                "grpc_port": f"{self.port_prefix}{num}{90}",
                "app_port": f"{self.port_prefix}{num}{56}",
                "rpc_port": f"{self.port_prefix}{num}{57}",
                "abci_port": f"{self.port_prefix}{num}{58}",
                "pprof_port": f"{self.port_prefix}{num}{60}",
                "feeder_port": f"{self.port_prefix}{num}{71}",
                "persistent_peers": ",".join(persistent_peers),
                "moniker": info["moniker"],
                "address": info["address"],
                "valoper": info["valoper"],
                "chain_id": self.chain_id,
                "podman": self.podman
            }

            open(f"{home}/config/app.toml", "w").write(
                app_toml.render(config)
            )

            open(f"{home}/config/config.toml", "w").write(
                config_toml.render(config)
            )

            if self.denom != "ukuji":
                continue

            home = f"{WORKDIR}/feeder{num}"
            if os.path.isdir(home):
                continue

            os.mkdir(home)

            open(f"{home}/config.toml", "w").write(
                feeder_toml.render(config)
            )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--nodes", type=int, default=1,
                        help="Set number of validator nodes")
    parser.add_argument("--clear", action="store_true",
                        help="Remove all configs and create new chain")
    parser.add_argument("--podman", action="store_true",
                        help="Generate start/stop scripts for podman")

    return parser.parse_args()


def main():
    args = parse_args()

    if args.clear:
        shutil.rmtree(WORKDIR, ignore_errors=True)

    if not os.path.isdir(WORKDIR):
        os.mkdir(WORKDIR)

    config = {
        "command": "docker",
        "chains": {}
    }

    if args.podman:
        config["command"] = "podman"

    chains = [
        Chain("Kujira", "pond-1", "ukuji", args.nodes, 1, args.podman),
        # Chain("Faker", "faker-1", "ufake", 1, 2)
    ]

    for chain in chains:
        chain_info = {
            "name": chain.name,
            "validators": []
        }

        for validator in chain.validators:
            validator["rpc_url"] = f"http://localhost:{validator['rpc_port']}"
            validator["api_url"] = f"http://localhost:{validator['api_port']}"
            validator.pop("rpc_port")
            validator.pop("api_port")
            validator.pop("amount")

            chain_info["validators"].append(validator)

        config["chains"][chain.chain_id] = chain_info

    json.dump(config, open(f"{WORKDIR}/pond.json", "w"))


if __name__ == "__main__":
    main()

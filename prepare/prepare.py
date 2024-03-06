#!/usr/bin/env python3

import json
import shutil
import subprocess
import os
import jinja2
import argparse

WORKDIR = "pond"


class Node:
    denom = ""
    chain_id = ""
    port_prefix = 0
    home = ""
    binary = ""

    def __init__(self, name, chain_id, binary, denom, port_prefix):
        self.name = name
        self.home = f"{WORKDIR}/{name}"
        self.chain_id = chain_id
        self.binary = binary
        self.port_prefix = port_prefix
        self.denom = denom

    def init(self):
        result = subprocess.check_output([
            self.binary, "--home", self.home, "init", self.name,
            "--chain-id", self.chain_id, "--default-denom", self.denom
        ], stderr=subprocess.STDOUT)

        output = json.loads(result)

        return output["node_id"]

    def add_key(self, name, mnemonic, dryrun=False):
        extra = []
        if dryrun:
            extra = ["--dry-run"]

        result = subprocess.run([
            self.binary, "--output", "json",
            "--home", self.home, "keys", "add", name,
            "--keyring-backend", "test", "--recover"
        ] + extra, capture_output=True, text=True, input=mnemonic)

        output = json.loads(result.stdout)
        address = output["address"]

        return address

    def add_genesis_account(self, address, amount):
        subprocess.run([
            self.binary, "--output", "json", "--home", self.home, "genesis",
            "add-genesis-account", address, f"{amount}{self.denom}"
        ])

    def create_gentx(self, amount):
        subprocess.check_call([
            self.binary, "--output", "json", "--home", self.home, "genesis",
            "gentx", "validator", f"{amount}{self.denom}",
            "--chain-id", self.chain_id, "--keyring-backend", "test"
        ], stderr=subprocess.DEVNULL)

        gentx_path = f"{self.home}/config/gentx"
        gentx_file = os.listdir(gentx_path)[0]
        gentx_data = json.load(open(f"{gentx_path}/{gentx_file}", "r"))
        valoper = gentx_data["body"]["messages"][0]["validator_address"]

        return valoper

    def collect_gentxs(self):
        subprocess.check_output([
            self.binary, "--home", self.home, "genesis", "collect-gentxs"
        ], stderr=subprocess.DEVNULL)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--nodes", type=int, default=1,
                        choices=range(1, 9), metavar="[1-9]",
                        help="Set number of validator nodes")
    parser.add_argument("--clear", action="store_true",
                        help="Remove all configs and create new chain")
    parser.add_argument("--podman", action="store_true",
                        help="Generate start/stop scripts for podman")

    return parser.parse_args()


def get_persistent_peers(validators, node_id, podman):
    persistent_peers = []
    for validator in validators:
        if validator["node_id"] == node_id:
            continue

        port = validator["app_port"]
        host = validator["moniker"].lower()
        peer = validator["node_id"]
        if podman:
            host = "127.0.0.1"
        persistent_peers.append(f"{peer}@{host}:{port}")

    return persistent_peers


def init_chain(prefix, chain_id, binary, denom, nodes, port_prefix, mnemonics, podman):
    info = {
        "validators": [],
        "accounts": {}
    }

    total = 0

    main = Node(f"{prefix}1", chain_id, binary, denom, port_prefix)

    for i in range(nodes):
        moniker = f"{prefix}{i+1}"
        mnemonic = mnemonics["validators"][i]

        amount = 300_000_000_000
        staked = 200_000_000_000

        total += amount

        node = Node(moniker, chain_id, binary, denom, port_prefix)
        node_id = node.init()
        address = node.add_key("validator", mnemonic)
        node.add_genesis_account(address, amount)
        valoper = node.create_gentx(staked)

        # add account to "main" node
        if i > 0:
            main.add_genesis_account(address, amount)

        info["validators"].append({
            "moniker": moniker,
            "address": address,
            "valoper": valoper,
            "node_id": node_id,
            "mnemonic": mnemonic,
            "api_port": f"{port_prefix}{i+1:02}17",
            "app_port": f"{port_prefix}{i+1:02}56",
            "rpc_port": f"{port_prefix}{i+1:02}57",
            "feeder_url": f"http://localhost:10{i+1}71/api/v1/prices"
        })

        if i == 0:
            continue

        gentx_path = f"{WORKDIR}/{moniker}/config/gentx"
        gentx_file = os.listdir(gentx_path)[0]

        shutil.copyfile(
            f"{gentx_path}/{gentx_file}",
            f"{WORKDIR}/{prefix}1/config/gentx/{gentx_file}"
        )

    for i in range(0, len(mnemonics.get("accounts", []))):
        name = f"test{i}"
        mnemonic = mnemonics["accounts"][i]

        amount = 10_000_000_000_000
        total += amount

        address = main.add_key(name, mnemonic)
        main.add_genesis_account(address, amount)

        info["accounts"][name] = {
            "address": address,
            "mnemonic": mnemonic
        }

    # add special accounts
    for name in ["relayer", "deployer"]:
        mnemonic = mnemonics[name]

        amount = 1_000_000_000_000
        total += amount

        address = main.add_key(name, mnemonic)
        main.add_genesis_account(address, amount)

        info["accounts"][name] = {
            "address": address,
            "mnemonic": mnemonic
        }

    main.collect_gentxs()

    genesis = json.load(open(f"{main.home}/config/genesis.json"))

    genesis["app_state"]["crisis"]["constant_fee"]["denom"] = denom
    genesis["app_state"]["denom"]["params"]["creation_fee"][0]["denom"] = denom
    genesis["app_state"]["gov"]["params"]["min_deposit"][0]["denom"] = denom
    genesis["app_state"]["gov"]["params"]["max_deposit_period"] = "20s"
    genesis["app_state"]["gov"]["params"]["voting_period"] = "20s"
    genesis["app_state"]["mint"]["minter"]["inflation"] = "0"
    genesis["app_state"]["mint"]["params"]["mint_denom"] = denom
    genesis["app_state"]["staking"]["params"]["unbonding_time"] = "1209600s"
    genesis["app_state"]["staking"]["params"]["bond_denom"] = denom
    genesis["consensus"]["params"]["abci"]["vote_extensions_enable_height"] = "1"

    if chain_id == "pond-1":
        genesis["app_state"]["oracle"]["params"]["whitelist"] = [
            {"name": "BTC"},
            {"name": "ETH"}
        ]

    for i in range(nodes):
        filename = f"{WORKDIR}/{prefix}{i+1}/config/genesis.json"
        json.dump(genesis, open(filename, "w"))

    app_toml = jinja2.Template(
        open("templates/app.toml.j2", "r").read()
    )
    config_toml = jinja2.Template(
        open("templates/config.toml.j2", "r").read()
    )
    client_toml = jinja2.Template(
        open("templates/client.toml.j2", "r").read()
    )
    feeder_toml = jinja2.Template(
        open("templates/feeder.toml.j2", "r").read()
    )

    for i, validator in enumerate(info["validators"]):
        # validator nodes

        home = f"{WORKDIR}/{prefix}{i+1}"

        node_id = validator["node_id"]

        persistent_peers = get_persistent_peers(
            info["validators"], node_id, podman
        )

        config = {
            "api_port": f"{port_prefix}0{i+1}{17}",
            "grpc_port": f"{port_prefix}0{i+1}{90}",
            "app_port": f"{port_prefix}0{i+1}{56}",
            "rpc_port": f"{port_prefix}0{i+1}{57}",
            "abci_port": f"{port_prefix}0{i+1}{58}",
            "pprof_port": f"{port_prefix}0{i+1}{60}",
            "feeder_port": f"{port_prefix}0{i+1}{71}",
            "persistent_peers": ",".join(persistent_peers),
            "moniker": validator["moniker"],
            "address": validator["address"],
            "valoper": validator["valoper"],
            "chain_id": chain_id,
            "node_num": i+1,
            "podman": podman
        }

        open(f"{home}/config/app.toml", "w").write(
            app_toml.render(config)
        )

        open(f"{home}/config/config.toml", "w").write(
            config_toml.render(config)
        )

        open(f"{home}/config/client.toml", "w").write(
            client_toml.render(config)
        )

        # feeders
        if chain_id != "pond-1":
            continue

        home = f"{WORKDIR}/feeder1-{i+1}"

        if not os.path.isdir(home):
            os.mkdir(home)

        open(f"{home}/config.toml", "w").write(
            feeder_toml.render(config)
        )

    # fix info

    for i in range(nodes):
        validator = info["validators"][i]

        validator["api_url"] = f"http://localhost:{validator['api_port']}"
        validator["app_url"] = f"tcp://localhost:{validator['app_port']}"
        validator["rpc_url"] = f"http://localhost:{validator['rpc_port']}"
        validator.pop("app_port")
        validator.pop("api_port")
        validator.pop("rpc_port")
        if chain_id != "pond-1":
            validator.pop("feeder_url")

        info["validators"][i] = validator

    return info


def main():
    args = parse_args()

    if args.clear:
        shutil.rmtree(WORKDIR, ignore_errors=True)

    if not os.path.isdir(WORKDIR):
        os.mkdir(WORKDIR)

    config = {
        "command": "docker",
        "wallets": {},
        "validators": {},
        "version": {
            "kujira": os.environ.get("KUJIRA_VERSION"),
            "feeder": os.environ.get("FEEDER_VERSION"),
            "relayer": os.environ.get("RELAYER_VERSION"),
            "prepare": os.environ.get("PREPARE_VERSION")
        }
    }

    if args.podman:
        config["command"] = "podman"

    mnemonics = json.load(open("mnemonics.json", "r"))

    info1 = init_chain(
        "kujira1-", "pond-1", "kujirad", "ukuji",
        args.nodes, 1, mnemonics, args.podman
    )

    info2 = init_chain(
        "kujira2-", "pond-2", "kujirad", "ukuji", 1, 2, mnemonics, args.podman
    )

    config["validators"] = {
        "pond-1": info1["validators"],
        "pond-2": info2["validators"]
    }

    config["accounts"] = info1["accounts"]

    # init relayer

    home = f"{WORKDIR}/relayer"
    os.makedirs(f"{home}/config", exist_ok=True)

    relayer_yaml = jinja2.Template(
        open("templates/relayer.yaml.j2", "r").read()
    )

    open(f"{home}/config/config.yaml", "w").write(
        relayer_yaml.render({"podman": args.podman})
    )

    shutil.copytree("keys", f"{home}/keys", dirs_exist_ok=True)

    json.dump(config, open(f"{WORKDIR}/pond.json", "w"))


if __name__ == "__main__":
    main()

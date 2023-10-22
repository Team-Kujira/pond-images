#!/usr/bin/env python3

import argparse
import requests
import base64
import subprocess
import json
import hashlib


class Chain:
    def __init__(self, binary, chain_id):
        self.binary = binary
        self.chain_id = chain_id
        # self.mnemonic = mnemonic

        # self.add_key()

        # get address
        result = subprocess.run([
            binary, "keys", "show", "validator", "-a"
        ], text=True, capture_output=True)

        self.address = result.stdout

    def add_key(self):
        cmd = [
            self.binary, "--home", "/Users/christian/.pond/kujira01",
            "keys", "add", "validator", "--recover", "--keyring-backend", "test"
        ]

        print(" ".join(cmd))

        result = subprocess.run(
            cmd, text=True, input=self.mnemonic, capture_output=True
        )

        print(result.stderr)
        print(result.stdout)

    def q(self, args):
        cmd = [self.binary, "--home", "/Users/christian/.pond/kujira01", "q"] + args.split() + [
            "--node", "http://127.0.0.1:10157",
            "--chain-id", self.chain_id, "--output", "json"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        return result.stdout

    def tx(self, args):
        cmd = [self.binary, "--home", "/Users/christian/.pond/kujira01", "tx"] + args.split() + [
            "--node", "http://127.0.0.1:10157",
            "--chain-id", self.chain_id, "--output", "json",
            "--from", "validator", "--keyring-backend", "test",
            "--gas", "auto", "--gas-adjustment", "2", "--yes"
        ]
        print(" ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True)

        print(result.stderr)
        print(result.stdout)

        return result.stdout

    def create_denom(self, denom):
        self.tx(f"denom create-denom {denom}")

    def add_orca_queue(self, usk, denom):
        params = {
            "bid_denom": f"factory/{self.address}/uusk",
            "bid_threshold": "10000000000",
            "collateral_denom": "factory/{self.address}/usquid",
            "fee_address": "kujira17xpfvakm2amg962yls6f84z3kell8c5lp3pcxh",
            "liquidation_fee": "0.01",
            "max_slot": 30,
            "owner": self.address,
            "premium_rate_per_slot": "0.01",
            "waiting_period": 600,
            "withdrawal_fee": "0.005"
        }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--rpc", default="https://rest.cosmos.directory/kujira")
    return parser.parse_args()


def main():
    args = parse_args()

    kujira = Chain(
        "kujirad-v0.8.8-43-gc5a82f3", "pond-1")

    contracts = {
        "usk_market": [73],
    }

    # for name, ids in contracts.items():
    #     for id in ids:
    #         url = f"{args.rpc}/cosmwasm/wasm/v1/code/{id}"
    #         print(url)
    #         response = requests.get(url)

    #         if response.status_code != 200:
    #             raise f"response status: {response.status_code}"

    #         data = response.json().get("data")
    #         if not data:
    #             raise "data is None"

    #         bz = base64.b64decode(data)

    #         open(f"{id}.wasm", "wb").write(bz)

    #         print(hashlib.sha256(bz).hexdigest())

    #         # print(kujira.tx(f"wasm stor1 {id}.wasm"))
    #         print(kujira.q(f"wasm code-info 1"))

    kujira.create_denom("ufoo")


if __name__ == "__main__":
    main()

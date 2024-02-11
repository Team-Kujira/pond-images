#!/usr/bin/env python3

import argparse
import requests
import base64
import subprocess
import json
import hashlib
import time
import logging
import sys


class Chain:
    def __init__(self, binary, chain_id):
        self.binary = binary
        self.chain_id = chain_id

        self.accounts = {}
        self.denoms = {}
        self.contracts = {}

        # get address
        result = subprocess.run([
            binary, "keys", "show", "validator", "-a", "--keyring-backend", "test", "--home", "/Users/christian/.pond/kujira01"
        ], text=True, capture_output=True)

        self.address = result.stdout.strip()

        result = self.q("auth accounts")
        for account in result["accounts"]:
            name = account.get("name")
            if not name:
                continue

            self.accounts[name] = account["base_account"]["address"]

    def q(self, args):
        cmd = [self.binary, "--home", "/Users/christian/.pond/kujira01", "q"] + args.split() + [
            "--node", "http://127.0.0.1:10157",
            "--chain-id", self.chain_id, "--output", "json"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(result.stderr)
            return None

    def tx(self, args):
        time.sleep(8)
        cmd = [self.binary, "--home", "/Users/christian/.pond/kujira01", "tx"] + args.split() + [
            "--node", "http://127.0.0.1:10157",
            "--chain-id", self.chain_id, "--output", "json",
            "--from", "validator", "--keyring-backend", "test",
            "--gas", "auto", "--gas-adjustment", "2", "--yes",
            "-b", "async"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(result.stderr)
            print(result.stdout)
            return None

        return json.loads(result.stdout)

    def wait_for(self, tx, timeout=10):
        print(f"wait for tx: {tx}")
        result = None
        while result == None and timeout > 0:
            print(timeout)
            time.sleep(1)
            timeout -= 1
            result = self.q(f"tx {tx}")

        # if result.returncode != 0:
        #     print(result)

    def create_denom(self, denom):
        logging.info(f"create {denom}")

        path = f"factory/{self.address}/u{denom}".lower()
        self.denoms[path] = denom

        return {
            "@type": "/kujira.denom.MsgCreateDenom",
            "sender": self.address,
            "nonce": f"u{denom}".lower()
        }

    def instantiate_fin_contract(self, denom1, denom2, precision=4, delta=0):
        logging.info(f"Instantiate Fin pair {denom1}/{denom2}")

        path1 = ""
        path2 = ""
        for path, denom in self.denoms.items():
            if denom1 == denom:
                path1 = path
            if denom2 == denom:
                path2 = path

        code_id = 2
        label = f"FIN pair {denom1}/{denom2}"

        return {
            "@type": "/cosmwasm.wasm.v1.MsgInstantiateContract",
            "sender": self.address,
            "admin": self.address,
            "code_id": f"{code_id}",
            "label": label,
            "msg": {
                "owner": self.address,
                "denoms": [
                    {"native": path1},
                    {"native": path2}
                ],
                "price_precision": {
                    "decimal_places": 4
                },
                "decimal_delta": 0,
                "fee_taker": "0.0015",
                "fee_maker": "0.00075"
            },
            "funds": []
        }

    def instantiate_orca_queue(self, source, collateral, denom):
        params = {
            # "bid_denom": f"factory/{self.address}/uusk",
            "bid_denom": denom,
            "bid_threshold": "10000000000",
            # "collateral_denom": f"factory/{self.address}/usquid",
            "collateral_denom": collateral,
            "fee_address": self.accounts["fee_collector"],
            "liquidation_fee": "0.01",
            "max_slot": 30,
            "owner": self.address,
            "premium_rate_per_slot": "0.01",
            "waiting_period": 600,
            "withdrawal_fee": "0.005"
        }

    def send(self, messages):
        tx = {
            "body": {
                "messages": messages,
                "memo": "",
                "timeout_height": "0",
                "extension_options": [],
                "non_critical_extension_options": []
            },
            "auth_info": {
                "signer_infos": [],
                "fee": {
                    "amount": [],
                    "gas_limit": "1000000000",
                    "payer": "",
                    "granter": ""
                },
                "tip": None
            },
            "signatures": []
        }

        tx_file = "/tmp/tx.json"

        open(tx_file, "w").write(json.dumps(tx))

        result = self.tx(f"sign {tx_file}")

        if not result:
            return

        open(f"{tx_file}.signed", "w").write(json.dumps(result))

        result = self.tx(f"broadcast {tx_file}.signed")

        self.wait_for(result["txhash"])

    def get_contracts(self):
        contracts = {}
        result = self.q("wasm list-codes")
        for index in range(len(result["code_infos"])):
            id = index + 1
            contracts[id] = {}
            result = self.q(f"wasm list-contract-by-code {id}")
            for contract in result["contracts"]:
                result = self.q(f"wasm contract {contract}")
                contracts[id][contract] = result["contract_info"]["label"]

        print(json.dumps(contracts, indent=2))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--rpc", default="https://api-kujira.starsquid.io")
    # "--rpc", default="https://rest.cosmos.directory/kujira")
    return parser.parse_args()


def main():
    args = parse_args()

    kujira = Chain(
        "kujirad-v0.8.8-43-gc5a82f3", "pond-1")

    contracts = [{
        "name": "usk_market",
        "id": 73
    }, {
        "name": "fin",
        "id": 134
    }]

    kujira.get_contracts()

    result = kujira.q("wasm list-codes")
    if result["code_infos"]:
        # contracts already deployed, exit
        sys.exit(0)

    messages = []

    for contract in contracts:
        id = contract["id"]
        url = f"{args.rpc}/cosmwasm/wasm/v1/code/{id}"
        response = requests.get(url)

        print(url)

        if response.status_code != 200:
            print(f"response status: {response.status_code}")
            sys.exit(1)

        data = response.json().get("data")
        if not data:
            raise "data is None"

        bz = base64.b64decode(data)

        messages.append({
            "@type": "/cosmwasm.wasm.v1.MsgStoreCode",
            "sender": kujira.address,
            "wasm_byte_code": data,
            "instantiate_permission": None
        })

    for denom in ["USK", "SQUID"]:
        messages.append(kujira.create_denom(denom))

    print("Deploy contracts")
    # kujira.send(messages)

    print(kujira.denoms)

    messages = [kujira.instantiate_fin_contract("SQUID", "USK")]

    print("Instantiate contracts")
    kujira.send(messages)


if __name__ == "__main__":
    main()

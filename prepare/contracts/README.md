# contract deployer

## Requirements

- python3-mako
- python3-requests
- python3-yaml

## Usage

The deployment is a wrapper around <https://github.com/Team-Kujira/core> and therefore needs a working kujirad binary as well as a funded wallet for the required transactions. It is designed for pond, but should also work on testnet (see `--help` for parameters)

```sh
./deploy.py --node http://localhost:10157 plans/kujira.yml
```

### Registry

The `registry.yml` provides a reference to the compiled code, as well as the expected hash. Currently only mainnet is available as source, more options will be added in the future.

Example:

```yaml
kujira_fin:
  checksum: 8A6FA03E62DA9CB75F1CB9A4EFEA6AAFA920AD5FCA40A7B335560727BD42C198
  source: kaiyo-1://243
```

### Plan files

Plan files define the params and order of the contracts that should be deployed and denoms that need to be created. After each contract deployment, the deployer queries its address and `{"config":{}}` output which can then be referenced in later steps by the its deployment `name`. Denoms are handled at first and can be referenced as well.

Already existing code, denoms and contracts won't be deployed or instantiated again.

Example:

```yml
denoms:
  - name: KUJI
    path: ukuji
  - name: USK
    nonce: uusk

contracts:
  - name: kujira_fin_kuji_usk
    code: kujira_fin
    label: FIN KUJI-USK
    msg:
      denoms:
        - native: ${denoms.KUJI.path}
        - native: ${denoms.USK.path}
      price_precision:
        decimal_places: 4
      decimal_delta: 0
      fee_taker: "0.0015"
      fee_maker: "0.00075"

  - name: kujira_bow_kuji_usk
    code: kujira_bow_xyk
    label: BOW KUJI-USK
    funds: 10000000ukuji
    msg:
      fin_contract: ${contracts.kujira_fin_kuji_usk.address}
      intervals:
        - "0.01"
        - "0.05"
      fee: "0.1"
      amp: "1"
```

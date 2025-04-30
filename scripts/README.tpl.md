# Open Price ETH Data Repository
Open Price ETH is an open-data initiative providing a standardized, continuously updated historical dataset of ETH/USD prices from on-chain sources (Chainlink and Uniswap V3 soon). Fully compliant with FAIR principles, it empowers researchers and developers with transparent, reproducible insights into Ethereum price dynamics.

---

## 📅 Available Datasets

| Dataset                | Start Date Available       | End Date Available     | CSV File                                          | Extraction Script                 |
|------------------------|----------------------------|------------------------|---------------------------------------------------|-----------------------------------|
| **Chainlink ETH/USD**  | 2020-08-07 11:28:13 UTC    | {{ chainlink.extraction  }}| `data/chainlink_eth_usd.csv`                      | `scripts/chainlink_dicho.py`      |
| **Uniswap V3 ETH/USDC**| 2020-05-04 00:00:00 UTC    | {{ uniswap.extraction    }}| `data/uniswap_eth_usd.csv`                        | `scripts/Uniswap_process_logs.py` |

Extraction date and time are taken from the CSV file’s last modification timestamp.

*(More datasets coming soon: Uniswap V2, etc.)*

---

## 🗂 CSV Structure: `chainlink_eth_usd.csv`

This file contains hourly Ether prices in USD from the Chainlink oracle on the Ethereum Mainnet.

| Column             | Type    | Description                                                                                     |
|--------------------|---------|-------------------------------------------------------------------------------------------------|
| `global_round_id`  | uint80  | Global round identifier (`phase << 64 | aggregator_round_id`)                                   |
| `phase`            | int     | Chainlink contract phase identifier                                                             |
| `aggregator_round` | int     | Round identifier within the given phase                                                         |
| `datetime_utc`     | string  | Update timestamp in `YYYY-MM-DD HH:MM:SS` format (UTC)                                          |
| `price`            | float   | ETH/USD price (converted from the integer returned by Chainlink, which is scaled by 10⁸)        |



### 🗂 CSV Structure: `data/uniswap_eth_usd.csv`

| Column               | Type    | Description                                                                                       |
|----------------------|---------|---------------------------------------------------------------------------------------------------|
| `timestamp`          | string  | UTC timestamp with timezone, e.g. `2024-04-19 23:59:59+00:00`                                     |
| `price_usdc_per_eth` | float   | Price expressed in USDC per ETH                                                                  |
| `usdc_amount`        | float   | Quantité de USDC transférée                                                                      |
| `eth_amount`         | float   | Quantité d’ETH transférée                                                                        |
| `volume_usdc`        | float   | Volume total en USDC de la transaction                                                           |
| `block_number`       | int     | Numéro du bloc Ethereum                                                                          |
| `transaction_hash`   | string  | Hash de la transaction                                                                           |



---

## 🛠️ Auto-Generating the README

We use a Jinja2 template plus a Python script to inject the extraction date automatically based on the CSV’s last-modified timestamp

**Install dependencies**  
   pip install -r requirements.txt

---

## 🧾 License

All contents of this repository (data, code, and documentation) are licensed under the  
[Creative Commons Attribution 4.0 International License (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).  

You are free to use, adapt, and share, **as long as you credit the original authors**:  
**HEG Geneva / Deep Mining Lab / FairOnChain / Open Price ETH**
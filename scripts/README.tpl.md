# EtherFAIR Data Repository
EtherFAIR is an open-data initiative providing a standardized, continuously updated historical dataset of ETH/USD prices from on-chain sources (Chainlink and Uniswap V3 soon). Fully compliant with FAIR principles, it empowers researchers and developers with transparent, reproducible insights into Ethereum price dynamics.

---

## 📅 Available Datasets

| Dataset               | Start Date Available       | End Date Available                   | CSV File                                          | Extraction Script              |
|-----------------------|----------------------------|--------------------------------------|---------------------------------------------------|--------------------------------|
| **Chainlink ETH/USD** | 2020-08-07 11:28:13 UTC    | {{ chainlink.extraction ~ "      " }}| `data/chainlink_eth_usd.csv`                      | `scripts/chainlink_dicho.py`   |

Extraction date and time are taken from the CSV file’s last modification timestamp.

*(More datasets coming soon: Uniswap V3, etc.)*

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

---

## 🛠️ Auto-Generating the README

We use a Jinja2 template plus a Python script to inject the extraction date automatically based on the CSV’s last-modified timestamp

**Install dependencies**  
   pip install jinja2

---

## 🧾 License

This project is licensed under the MIT License (./LICENSE)
You are free to use, modify, distribute the source code and the data associated  
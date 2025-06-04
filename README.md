# Open Price ETH Data Repository
Open Price ETH is an open-data initiative providing a standardized, continuously updated historical dataset of ETH/USD prices from on-chain sources (Chainlink and Uniswap V3). Fully compliant with FAIR principles, it empowers researchers and developers with transparent, reproducible insights into Ethereum price dynamics.

---

## 📅 Available Datasets

| Dataset                | Start Date Available       | End Date Available     | CSV File                                          |
|------------------------|----------------------------|------------------------|---------------------------------------------------|
| **Chainlink ETH/USD**  | 2020-08-07 11:28:13 UTC    | 2025-06-04 08:00:35 UTC| `data/chainlink_eth_usd.csv`                      |    
| **Uniswap V3 ETH/USDC**| 2021-05-05 22:15:01 UTC    | 2025-06-04 08:05:23 UTC| `data/uniswap_eth_usd.csv`                        | 

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


## 🗂 CSV Structure: `uniswap_eth_usd.csv`

| Column               | Type    | Description                                                                                   |
|----------------------|---------|-----------------------------------------------------------------------------------------------|
| `timestamp`          | string  | UTC timestamp with timezone, e.g. `2024-04-19 23:59:59+00:00`                                 |
| `price_usdc_per_eth` | float   | Price expressed in USDC per ETH                                                               |
| `usdc_amount`        | float   | Quantité de USDC transférée                                                                   |
| `eth_amount`         | float   | Quantité d’ETH transférée                                                                     |
| `volume_usdc`        | float   | Volume total en USDC de la transaction                                                        |
| `block_number`       | int     | Numéro du bloc Ethereum                                                                       |
| `transaction_hash`   | string  | Hash de la transaction                                                                        |

---

## 📊 Chainlink ETH/USD Data Extraction Method

The script `chainlink_dicho.py` retrieves the complete history of ETH/USD prices from the Chainlink contract on Ethereum Mainnet. Here's a detailed explanation of how the extraction process works:

### Technical Details

1. **Data Source**:
   - Chainlink ETH/USD contract on Ethereum Mainnet: `0x5f4ec3df9cbd43714fe2740f5e3616155c5b8419`
   - Interface used: Functions `latestRoundData()` and `getRoundData(uint80 roundId)`

2. **Understanding Chainlink Round Identifiers**:
   - The Chainlink system uses a global round identifier composed of two parts:
     - `phaseId`: Identifies different versions or phases of the aggregation contract (16 bits)
     - `aggregatorRoundId`: Identifies a specific round within a phase (64 bits)
   - Format: `(phaseId << 64) | aggregatorRoundId`

3. **Extraction Algorithm**:
   - For each phase (from 1 up to the current phase):
     - Determine the maximum number of rounds in the phase via binary search
     - Identify temporal boundaries via binary searches:
       - First round after the targeted start date
       - Last round before the targeted end date
     - Sequential extraction of data for all rounds in the interval

4. **Search Optimizations**:
   - **Exponential search** to quickly find an approximate upper bound
   - **Binary search** to precisely determine:
     - The last valid round of a phase
     - The first round corresponding to the start timestamp
     - The last round corresponding to the end timestamp

5. **Post-processing**:
   - Chronological sorting of results by timestamp
   - Conversion of prices from Chainlink format (integer * 10⁸) to decimal values
   - Formatting timestamps into readable strings `YYYY-MM-DD HH:MM:SS`

### Implementation Specifics

- **Contract Phase Management**: The script goes through all Chainlink contract phases to ensure comprehensive coverage.
- **RPC Query Optimization**: Binary searches are used to minimize the number of calls to the RPC node.
- **Data Validation**: Filtering of invalid rounds (timestamp = 0) and handling of contract call errors.
- **Parameterized Time Range**: Ability to specify start and end timestamps to target a specific period.


To modify the extraction time range, adjust the `TIMESTAMP_DEBUT` and `TIMESTAMP_FIN` variables in the script.

---

## 📊 Uniswap V3 ETH/USDC Data Extraction Method

## 1. Cryo Extraction

cryo logs \
  --address 0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640 \
  --rpc https://eth.rpc.faironchain.org/ \
  --output-dir ./output \
  --csv \
  --timestamps <start_timestamp>:<end_timestamp>


| Option         | Description                                             |
|----------------|---------------------------------------------------------|
| `--address`    | Uniswap V3 WETH/USDC pool contract (0.05% fee tier)     |
| `--rpc`        | Ethereum Mainnet RPC endpoint                           |
| `--output-dir` | Directory for raw CSV logs                              |
| `--csv`        | Output in CSV format                                    |
| `--timestamps` | Time range filter (`<start_timestamp>:<end_timestamp>`) |

## 2. Filtering & Decoding Swap Events

The script `Uniswap_process_logs.py` process Cryo-extracted Uniswap V3 WETH/USDC logs, decodes swap events to compute and timestamp ETH prices, and outputs a consolidated CSV.

**Script**: `scripts/Uniswap_process_logs.py`  
**Input**: `data/output/*.csv`  
**Event Signature**: `0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67`

**Decoding Fields**:
- `amount0` (int256): USDC amount (6 decimals)
- `amount1` (int256): WETH amount (18 decimals)
- `sqrtPriceX96` (uint160): √Price Q96 format

## 3. Price Calculation

1. **Compute root price**:  
   `sqrt_price = sqrtPriceX96 / 2**96`

2. **Square for ETH per USDC**:  
   `price_eth_per_usdc = sqrt_price**2`

3. **Adjust decimal offset** (12 decimals):  
   `price_eth_per_usdc_adj = price_eth_per_usdc * 1e-12`

4. **Invert for USDC per ETH**:  
   `price_usdc_per_eth = 1 / price_eth_per_usdc_adj`

## 4. Timestamp Enrichment

- Batch-fetch block timestamps via Web3 RPC to minimize requests
- Convert UNIX timestamps → UTC datetime with timezone

## 5. Volume Computation

volume_usdc = abs(usdc_amount) + abs(eth_amount * price_usdc_per_eth)

## 6. Result Aggregation

Collect and export to `data/uniswap_eth_usd.csv` with columns:
- timestamp
- price_usdc_per_eth
- usdc_amount
- eth_amount
- volume_usdc
- block_number
- transaction_hash

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
**HES-SO / HEG Geneva / Deep Mining Lab / FairOnChain / Open Price ETH**
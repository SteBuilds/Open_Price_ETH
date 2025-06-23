# SPDX-License-Identifier: CC-BY-4.0
# © 2025 HES-SO / HEG Geneva / Deep Mining Lab / FairOnChain / Open Price ETH

import csv
import time
import argparse
import os
import sys
from web3 import Web3
from datetime import datetime, timezone

# Définir l'argument début
parser = argparse.ArgumentParser(description="Timestamp de début.")
parser.add_argument(
    "--debut",
    type=int,
    required=True,
    help="Timestamp UNIX de début (ex. 1744610424)."
)
args = parser.parse_args()

# Lecture de la variable d'environnement RPC
RPC_URL = os.environ.get("RPC", "")
if not RPC_URL:
    print("ERREUR: la variable d'environnement 'RPC' n'est pas définie.", file=sys.stderr)
    sys.exit(1)

CONTRACT_ADDRESS = '0x5f4ec3df9cbd43714fe2740f5e3616155c5b8419' # Contrat Chainlink pour la pair ETH/USD sur Ethereum Mainnet
FILENAME = "data/chainlink_eth_usd_last.csv"

TIMESTAMP_DEBUT = args.debut        # Timestamp de début
TIMESTAMP_FIN   = int(time.time())  # timestamp actuel

if TIMESTAMP_DEBUT > TIMESTAMP_FIN:
    parser.error("Le paramètre --debut doit être inférieur ou égal au timestamp actuel !")

def convertir_timestamp(ts: int) -> str:
    """
    Convertit un timestamp UNIX en chaîne lisible 'YYYY-MM-DD HH:MM:SS'
    """
    if ts == 0:
        return "Invalid round (ts=0)"
    # return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(timespec='seconds') #ISO 8601
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S+00:00')

def to_round_id(phase: int, aggregator_id: int) -> int:
    """
    Compose un identifiant de round unique à partir du phaseId et aggregatorRoundId.
    Format: [phaseId sur 16 bits][aggregatorRoundId sur 64 bits]
    """
    return (phase << 64) | aggregator_id

def parse_round_id(round_id: int) -> (int, int):
    """
    Décompose un roundId global en ses composants phaseId et aggregatorRoundId.
    """
    phase_id = round_id >> 64
    aggregator_id = round_id & 0xFFFFFFFFFFFFFFFF
    return phase_id, aggregator_id

def find_max_aggregator_id(phase: int) -> int:
    """
    Trouve le plus grand aggregatorRoundId valide pour une phase donnée.
    Utilise une double stratégie:
    1. Recherche exponentielle pour trouver une borne supérieure
    2. Recherche dichotomique pour trouver la valeur exacte
    """
    low = 1
    high = 1
    # Phase 1: Trouver une borne supérieure initiale
    while True:
        round_id = to_round_id(phase, high)
        try:
            rd = contract.functions.getRoundData(round_id).call()
            if rd[3] != 0:  # Vérifie si updatedAt n'est pas nul
                low = high
                high *= 2   # Double la recherche
            else:
                break
        except:
            break
    # Phase 2: Recherche dichotomique précise
    max_agg = 0
    while low <= high:
        mid = (low + high) // 2
        round_id = to_round_id(phase, mid)
        try:
            rd = contract.functions.getRoundData(round_id).call()
            if rd[3] != 0:
                max_agg = mid   # Mise à jour du maximum connu
                low = mid + 1   # Explore la partie supérieure
            else:
                high = mid - 1  # Réduit la borne supérieure
        except:
            high = mid - 1      # Gestion des erreurs de contrat
    return max_agg

def find_first_aggregator_id(phase: int, max_agg_id: int, target_ts: int) -> int:
    """
    Trouve le premier round avec timestamp >= target_ts.
    Utilise une recherche dichotomique classique.
    """
    low, high, result = 1, max_agg_id, None
    while low <= high:
        mid = (low + high) // 2
        round_id = to_round_id(phase, mid)
        try:
            rd = contract.functions.getRoundData(round_id).call()
            updated_at = rd[3]
            if updated_at >= target_ts:
                result = mid
                high = mid - 1 # Continue à chercher plus bas
            else:
                low = mid + 1  # Monte dans la plage
        except:
            high = mid - 1     # En cas d'erreur, réduit la recherche
    return result

def find_last_aggregator_id(phase: int, max_agg_id: int, target_ts: int) -> int:
    """
    Trouve le dernier round avec timestamp <= target_ts.
    Logique inverse de find_first_aggregator_id.
    """
    low, high, result = 1, max_agg_id, None
    while low <= high:
        mid = (low + high) // 2
        round_id = to_round_id(phase, mid)
        try:
            rd = contract.functions.getRoundData(round_id).call()
            updated_at = rd[3]
            if updated_at <= target_ts:
                result = mid
                low = mid + 1   # Continue à chercher plus haut
            else:
                high = mid - 1  # Descend dans la plage
        except:
            high = mid - 1
    return result

# Initialisation de la connexion Ethereum
web3 = Web3(Web3.HTTPProvider(RPC_URL))

if not web3.is_connected():
        print(f"ERREUR: impossible de se connecter à l'endpoint RPC '{RPC_URL}'", file=sys.stderr)
        sys.exit(1)

print(f"Connexion au réseau établie: {web3.is_connected()}")

checksum_addr = Web3.to_checksum_address(CONTRACT_ADDRESS)

# ABI minimum pour lire latestRoundData et getRoundData
abi = '''[
  {"inputs":[],"name":"latestRoundData","outputs":[
    {"internalType":"uint80","name":"roundId","type":"uint80"},
    {"internalType":"int256","name":"answer","type":"int256"},
    {"internalType":"uint256","name":"startedAt","type":"uint256"},
    {"internalType":"uint256","name":"updatedAt","type":"uint256"},
    {"internalType":"uint80","name":"answeredInRound","type":"uint80"}
  ],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint80","name":"_roundId","type":"uint80"}],
   "name":"getRoundData","outputs":[
     {"internalType":"uint80","name":"roundId","type":"uint80"},
     {"internalType":"int256","name":"answer","type":"int256"},
     {"internalType":"uint256","name":"startedAt","type":"uint256"},
     {"internalType":"uint256","name":"updatedAt","type":"uint256"},
     {"internalType":"uint80","name":"answeredInRound","type":"uint80"}
   ],"stateMutability":"view","type":"function"}
]'''

# Création de l'objet contrat
contract = web3.eth.contract(address=checksum_addr, abi=abi)

def is_in_range(ts: int, start_ts, end_ts) -> bool:
    """
    Vérifie si ts (le timestampe) est compris dans [start_ts, end_ts].
    """
    if ts == 0:
        return False
    if start_ts is not None and ts < start_ts:
        return False
    if end_ts is not None and ts > end_ts:
        return False
    return True

# Récupération des informations du dernier round
latest_data = contract.functions.latestRoundData().call()
latest_round_id = latest_data[0]  # uint80
latest_phase, latest_aggregator_id = parse_round_id(latest_round_id)

print(f"Latest Round ID global: {latest_round_id}")
print(f" - phaseId = {latest_phase}")
print(f" - aggregatorRoundId = {latest_aggregator_id}")


all_results = []  # Stockage des résultats

# On boucle de la phase 1 jusqu'à la phase la plus récente
# Une phase = une version du contrat
for phase in range(1, latest_phase + 1):
    
    max_agg_id = find_max_aggregator_id(phase)

    if max_agg_id == 0:
        print(f"Phase {phase} ignorée (aucun round valide)")
        continue
    
    # Recherche des bons rounds id qui correspondent a notre plage temporelle
    first_agg = find_first_aggregator_id(phase, max_agg_id, TIMESTAMP_DEBUT)
    last_agg = find_last_aggregator_id(phase, max_agg_id, TIMESTAMP_FIN)
    
    if not first_agg or not last_agg or first_agg > last_agg:
        print(f"Phase {phase} hors plage temporelle")
        continue
    
    # Collecter les données entre first_agg et last_agg
    aggregator_id = first_agg
    while aggregator_id <= last_agg:
        round_id_global = to_round_id(phase, aggregator_id)
        try:
            rd = contract.functions.getRoundData(round_id_global).call()
            answer = rd[1]      # Prix ETH/USD
            updated_at = rd[3]  # Timestamp de mise à jour
            if is_in_range(updated_at, TIMESTAMP_DEBUT, TIMESTAMP_FIN):
                date_str = convertir_timestamp(updated_at)
                price = float(answer) / 1e8  # Conversion en décimal pour ETH/USD
                all_results.append({
                    "round_id_global": round_id_global,
                    "phase_id": phase,
                    "aggregator_round_id": aggregator_id,
                    "price": price,
                    "timestamp": updated_at,
                    "date_str": date_str
                })
                aggregator_id += 1
        except Exception as e:
            print(f"Erreur sur {round_id_global}: {str(e)}")
            break
        
    print(f"Fin de la phase {phase}, aggregator_round_id max = {aggregator_id - 1}")


# Trier par timestamp chronologiquement
all_results.sort(key=lambda x: x["timestamp"])


with open(FILENAME, mode='w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    
    writer.writerow(["global_round_id", "phase", "aggregator_round", "datetime_utc", "price"])
    
    for item in all_results:
        writer.writerow([
            item["round_id_global"],
            item["phase_id"],
            item["aggregator_round_id"],
            item["date_str"],
            item["price"]
        ])

print(f"\nTerminé. {len(all_results)} lignes écrites dans {FILENAME}.")
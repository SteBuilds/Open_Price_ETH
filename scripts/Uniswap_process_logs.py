# SPDX-License-Identifier: CC-BY-4.0
# © 2025 HES-SO / HEG Geneva / Deep Mining Lab / FairOnChain / Open Price ETH

import pandas as pd
from web3 import Web3
from datetime import datetime
from mpmath import mp
import os
import sys
import glob
import pytz

mp.dps = 50  # Applique une haute précision pour les calculs décimaux

# Lecture de la variable d'environnement RPC
RPC_URL = os.environ.get("RPC", "")
if not RPC_URL:
    print("ERREUR: la variable d'environnement 'RPC' n'est pas définie.", file=sys.stderr)
    sys.exit(1)

# Constants
EXPECTED_TOPIC0 = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67" # Event Swap

# gestion des chemins
here = os.path.dirname(__file__)
data_dir = os.path.join(here, os.pardir, 'data', 'output')
data_dir = os.path.normpath(data_dir)
pattern = os.path.join(data_dir, '*.csv')
csv_files = glob.glob(pattern)

def decode_swap_event(data_hex):
    """
    Décode les données de l'événement Swap depuis le format hex

    Répartition des champs dans data :
    amount0 : int256 → 256 bits
    amount1 : int256 → 256 bits
    sqrtPriceX96 : uint160 → 160 bits
    liquidity : uint128 → 128 bits
    tick : int24 → 24 bits (rempli sur 256 bits, car les types dans Ethereum sont alignés sur 32 octets)
    """
    try:
        # Enlever le préfixe '0x' s'il existe
        data = data_hex.replace('0x', '')

        amount0_hex = data[0:64]            # Premier 32 octets (int256)
        amount1_hex = data[64:128]          # Deuxième 32 octets (int256)
        sqrtPriceX96_hex = data[128:192]    # Occupe 32 octets -> 128 à 192 en hexa    

        # Conversion hex -> int
        amount0 = int.from_bytes(bytes.fromhex(amount0_hex), byteorder='big', signed=True)
        amount1 = int.from_bytes(bytes.fromhex(amount1_hex), byteorder='big', signed=True)        
        sqrtPriceX96 = int(sqrtPriceX96_hex, 16)
        
        # Conversion des montants avec décimales
        usdc_amount = mp.mpf(amount0) / 10**6   # USDC a 6 décimales
        eth_amount = mp.mpf(amount1) / 10**18   # ETH a 18 décimales
        
        return usdc_amount, eth_amount, sqrtPriceX96
    
    except Exception as e:
        print(f"Erreur dans decode_swap_event: {e}")
        print(f"Data hex reçue: {data_hex}")
        raise


def calculate_price(sqrtPriceX96, eth_amount, usdc_amount):
    """
    Calcule le prix de 1 ETH en USDC à partir de sqrtPriceX96
    """
    try:
        # Conversion en nombre décimal de haute précision
        sqrtPriceX96 = mp.mpf(sqrtPriceX96)
        
        # Calcul du prix brut (ETH par USDC)
        sqrt_price = sqrtPriceX96 / (2 ** 96)
        price_eth_per_usdc = sqrt_price ** 2  # token1 (ETH) par token0 (USDC)

        # Ajustement des décimales (USDC:6, ETH:18 → écart 12 décimales)
        price_eth_per_usdc_adj = price_eth_per_usdc * mp.mpf("1e-12")

        # Inversion pour obtenir USDC par ETH
        price_usdc_per_eth = 1 / price_eth_per_usdc_adj

        #print(f"1 ETH = {mp.nstr(price_usdc_per_eth, 6)} USDC")

        # Calcul du volume en USDC (valeur absolue)
        volume_usdc = abs(usdc_amount) + abs(eth_amount * price_usdc_per_eth)
    
        return price_usdc_per_eth, volume_usdc
        
    except Exception as e:
        print(f"Erreur dans calculate_price: {e}")
        print(f"sqrtPriceX96 reçu: {sqrtPriceX96}") 
        raise

def process_uniswap_logs(csv_path, web3):
    """
    Traite les logs Uniswap et crée un nouveau CSV avec timestamps et prix
    """
    try:
        # Lecture du CSV
        print(f"Lecture du fichier: {csv_path}")
        df = pd.read_csv(csv_path)
        print(f"Nombre de lignes dans le CSV: {len(df)}")
        print("Colonnes disponibles:", df.columns.tolist())
        
        # Vérifier que la colonne 'data' existe
        if 'data' not in df.columns:
            print("Erreur: La colonne 'data' n'existe pas dans le CSV")
            return pd.DataFrame()
        
        # Création des listes pour stocker les résultats
        usdc_amounts = []
        eth_amounts = []
        timestamps = []
        prices = []
        volumes = []
        processed_block_numbers = []
        tx_hashes = []

        # Récupérer tous les numéros de blocs uniques
        block_numbers = list(set(df['block_number'].tolist()))
        print(f"Nombre de blocs uniques à récupérer : {len(block_numbers)}")

        # Récupérer tous les blocs en une seule passe
        blocks = {}
        for bn in block_numbers:
            try:
                block = web3.eth.get_block(bn)
                blocks[bn] = datetime.fromtimestamp(block['timestamp'], tz=pytz.UTC)
            except Exception as e:
                print(f"Erreur sur le bloc {bn} : {e}")
                blocks[bn] = None
        
        total_rows = len(df)
        for index, row in df.iterrows():
            try:
                # Afficher la progression
                print(f"\nTraitement de la ligne {index + 1}/{total_rows}")

                # Vérifier que topic0 correspond à la signature de l'event Swap attendue
                if row['topic0'] != EXPECTED_TOPIC0:
                    print("Signature de l'événement ne correspond pas à un event de type Swap.")
                    continue
                
                # Décodage du prix
                usdc, eth, sqrtPriceX96 = decode_swap_event(row['data'])
                #sqrtPriceX96 = decode_swap_event(row['data'])

                 # Calcul du prix et volume
                price, volume = calculate_price(sqrtPriceX96, eth, usdc)
                #price = calculate_price(sqrtPriceX96)
                
                # Récupération du timestamp
                timestamp = blocks.get(row['block_number'])
                                
                # Enregistrement des données valides
                if timestamp:
                    usdc_amounts.append(usdc)
                    eth_amounts.append(eth)
                    volumes.append(volume)
                    timestamps.append(timestamp)
                    prices.append(price)
                    processed_block_numbers.append(row['block_number'])
                    tx_hashes.append(row['transaction_hash'])
                
            except Exception as e:
                print(f"Erreur lors du traitement de la ligne {index}: {e}")
                continue
        
        print(f"\nNombre de prix valides collectés: {len(prices)}")
        
        if len(prices) == 0:
            print("Aucun prix valide n'a été collecté")
            return pd.DataFrame()
        
        # Création du nouveau DataFrame
        result_df = pd.DataFrame({
            'timestamp': timestamps,
            'price_usdc_per_eth': prices,
            'usdc_amount': usdc_amounts,
            'eth_amount': eth_amounts,
            'volume_usdc': volumes,
            'block_number': processed_block_numbers,
            'transaction_hash': tx_hashes
        })
        
        print(f"DataFrame créé avec {len(result_df)} lignes")
        print("\nAperçu des prix:")
        print(result_df['price_usdc_per_eth'].describe())
        
        return result_df
        
    except Exception as e:
        print(f"Erreur générale dans process_uniswap_logs: {e}")
        return pd.DataFrame()

def main(output_filename='uniswap_eth_usd_last.csv'):
    """
    Fonction principale pour traiter tous les fichiers CSV du dossier output
    """
    
    if not csv_files:
        print("Aucun fichier CSV trouvé dans le dossier 'output'")
        return None
    
    print(f"Fichiers CSV trouvés: {len(csv_files)}")
    for f in csv_files:
        print(f"- {f}")
    
    # Initialisation de la connexion Web3
    web3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not web3.is_connected():
        print(f"ERREUR: impossible de se connecter à l'endpoint RPC '{RPC_URL}'", file=sys.stderr)
        sys.exit(1)

    print(f"Connexion au réseau établie: {web3.is_connected()}")
    
    all_prices = pd.DataFrame()
    
    for csv_file in csv_files:
        prices = process_uniswap_logs(csv_file, web3)
        if not prices.empty:
            all_prices = pd.concat([all_prices, prices])
    
    if all_prices.empty:
        print("Aucune donnée n'a été traitée.")
        return None
    

    # Construction du chemin vers le dossier `data/`
    here2 = os.path.dirname(__file__)
    data_dir2 = os.path.normpath(os.path.join(here2, os.pardir, 'data'))
    output_path = os.path.join(data_dir2, output_filename)

    all_prices.to_csv(output_path, index=False)

    print(f"\nFichier CSV créé: {output_path}")
    print(f"Nombre total d'événements traités: {len(all_prices)}")
    
    return all_prices

if __name__ == "__main__":
    prices_df = main()
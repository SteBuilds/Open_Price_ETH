# SPDX-License-Identifier: CC-BY-4.0
# © 2025 HES-SO / HEG Geneva / Deep Mining Lab / FairOnChain / Open Price ETH

#!/usr/bin/env bash

# Description: Met à jour les données de Chainlink et d'Uniswap et concatène aux données existantes
# Usage: bash update.sh
# Pour les droits d'exécution: chmod +x update.sh

# Options de sécurité bash
set -euo pipefail

# Détecter le répertoire du script et définir le répertoire projet
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "$PROJECT_DIR"

# Créer le répertoire pour les logs
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
# Nom du fichier de log avec timestamp
LOG_FILE="$LOG_DIR/update_$(date +"%Y%m%d_%H%M%S").log"


echo "=== Démarrage du script update.sh ($(date)) ===" | tee -a "$LOG_FILE"
# Rediriger stdout et stderr vers le fichier de log (tout en conservant l'affichage)
exec > >(awk '{ print strftime("%Y-%m-%d %H:%M:%S"), "-", $0; fflush(); }' | tee -a "$LOG_FILE") 2>&1


# Chemins absolus
DATA_FILE_UNISWAP="$PROJECT_DIR/data/uniswap_eth_usd.csv"
DATA_FILE_CHAINLINK="$PROJECT_DIR/data/chainlink_eth_usd.csv"
OUTPUT_DIR="$PROJECT_DIR/data/output"
LAST_FILE_UNISWAP="$PROJECT_DIR/data/uniswap_eth_usd_last.csv"
LAST_FILE_CHAINLINK="$PROJECT_DIR/data/chainlink_eth_usd_last.csv"

# Afficher info RPC
if [[ -z "$RPC" ]]; then
  echo "WARNING: La variable RPC n'est pas définie." >&2
else
  echo "INFO: Utilisation de RPC=$RPC"
fi

# 1. Vérifier l'existence du CSV Uniswap & du CSV Chainlink 
if [[ ! -f "$DATA_FILE_UNISWAP" ]]; then
  echo "[ERROR] Fichier $DATA_FILE_UNISWAP introuvable." >&2
  exit 1
fi
echo "[INFO] Fichier de données: $DATA_FILE_UNISWAP"

if [[ ! -f "$DATA_FILE_CHAINLINK" ]]; then
  echo "[ERROR] Fichier $DATA_FILE_CHAINLINK introuvable." >&2
  exit 1
fi
echo "[INFO] Fichier de données: $DATA_FILE_CHAINLINK"

# 2. Récupérer et ajouter +1 seconde à la date de dernière modif des CSVs

# Extraire le champ “timestamp” de la dernière ligne des CSVs
last_iso_uniswap=$(tail -n 1 "$DATA_FILE_UNISWAP" | cut -d',' -f1)
last_iso_chainlink=$(tail -n 1 "$DATA_FILE_CHAINLINK" | cut -d',' -f4)

# Convertir ce timestamp ISO en secondes Unix puis +1
start_ts_uniswap=$(( $(date -d "$last_iso_uniswap" +"%s") + 1 ))
start_ts_chainlink=$(( $(date -d "$last_iso_chainlink" +"%s") + 1 ))

echo "[INFO] Timestamp de démarrage pour Uniswap (dernière date +1s) : $start_ts_uniswap"
echo "[INFO] Timestamp de démarrage pour Chainlink (dernière date +1s) : $start_ts_chainlink"

# 3. Lancer cryo logs avec timestamp
echo "[INFO] Lancement de 'cryo logs'..."

echo "$PROJECT_DIR"

cryo logs \
  --address 0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640 \
  --rpc $RPC \
  --output-dir $PROJECT_DIR/data/output \
  --csv \
  --timestamps ${start_ts_uniswap}: \
|| echo "[WARNING] 'cryo logs' a rencontré un problème... Le script continue..."

echo "[INFO] 'cryo logs' terminé"

# 4. Exécuter le traitement pour traiter les logs d'Uniswap

echo "[INFO] Vérification de la présence d'au moins un CSV dans $OUTPUT_DIR..."
if ! ls "$OUTPUT_DIR"/*.csv >/dev/null 2>&1; then
  echo "[ERROR] Aucun fichier CSV trouvé dans $OUTPUT_DIR. Impossible de lancer Uniswap_process_logs.py." >&2
  exit 1
fi

echo "[INFO] Lancement de Uniswap_process_logs.py..."
if ! python3 "$PROJECT_DIR/scripts/Uniswap_process_logs.py"; then
  echo "[ERROR] Échec de l’exécution de Uniswap_process_logs.py." >&2
  if ! rm -rf "$OUTPUT_DIR"/*; then
      echo "[WARNING] Impossible de supprimer le contenu de $OUTPUT_DIR." >&2
  fi
  exit 1
fi
echo "[INFO] Traitement Uniswap terminé"


# 5. Exécuter le traitement pour récupérer les prix de Chainlink
echo "[INFO] Lancement de chainlink_dicho.py..."
if ! python3 "$PROJECT_DIR/scripts/chainlink_dicho.py" --debut "$start_ts_chainlink"; then
  echo "[ERROR] Échec de l’exécution de chainlink_dicho.py." >&2
  if [[ -f "$LAST_FILE_CHAINLINK" ]]; then
    echo "[INFO] Suppression du fichier potentiellement corrompu : $LAST_FILE_CHAINLINK"
    if ! rm "$LAST_FILE_CHAINLINK"; then
      echo "[WARNING] Impossible de supprimer $LAST_FILE_CHAINLINK." >&2
    fi
  fi
  exit 1
fi
echo "[INFO] Traitement Chainlink terminé"

# 6. Nettoyer le contenu de data/output
echo "[INFO] Suppression du contenu de $OUTPUT_DIR"
# rm -rf "$OUTPUT_DIR"/*

if ! rm -rf "$OUTPUT_DIR"/*; then
      echo "[WARNING] Impossible de supprimer le contenu de $OUTPUT_DIR." >&2
fi


# 7. Concaténer uniswap_eth_usd_last.csv dans uniswap_eth_usd.csv et chainlink_eth_usd_last.csv dans chainlink_eth_usd.csv
if [[ -f "$LAST_FILE_UNISWAP" ]]; then
  echo "[INFO] Concaténation de $LAST_FILE_UNISWAP dans $DATA_FILE_UNISWAP"
  tail -n +2 "$LAST_FILE_UNISWAP" >> "$DATA_FILE_UNISWAP"
else
  echo "[WARNING] $LAST_FILE_UNISWAP non trouvé, aucune concaténation effectuée."
fi

if [[ -f "$LAST_FILE_CHAINLINK" ]]; then
  echo "[INFO] Concaténation de $LAST_FILE_CHAINLINK dans $DATA_FILE_CHAINLINK"
  tail -n +2 "$LAST_FILE_CHAINLINK" >> "$DATA_FILE_CHAINLINK"
else
  echo "[WARNING] $LAST_FILE_CHAINLINK non trouvé, aucune concaténation effectuée."
fi

# 8. Supprimer les fichiers une fois concaténés
if [[ -f "$LAST_FILE_UNISWAP" ]]; then
  echo "[INFO] Suppression de $LAST_FILE_UNISWAP"
  rm "$LAST_FILE_UNISWAP"
else
  echo "[WARNING] $LAST_FILE_UNISWAP n'a pas été supprimé."
fi

if [[ -f "$LAST_FILE_CHAINLINK" ]]; then
  echo "[INFO] Suppression de $LAST_FILE_CHAINLINK"
  rm "$LAST_FILE_CHAINLINK"
else
  echo "[WARNING] $LAST_FILE_CHAINLINK n'a pas été supprimé."
fi

# 9. MAJ du README
echo "[INFO] Lancement de generate_readme.py..."
if ! python3 "$PROJECT_DIR/scripts/generate_readme.py"; then 
  echo "[WARNING] Impossible de mettre à jour le README !" >&2
fi

echo "[INFO] Generate_readme terminé"

# Fin du script
echo "=== Fin du script ==="
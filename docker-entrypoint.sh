#!/usr/bin/env bash

cd /app || exit 1

# RPC
RPC=${RPC:-"https://ethereum-rpc.publicnode.com"}
export RPC

# Gérer le paramètre d'intervalle en jours
INTERVAL_DAYS=${INTERVAL_DAYS:-0}  # Valeur par défaut: 0 (exécution unique)

if [[ ! "$INTERVAL_DAYS" =~ ^[0-9]+$ ]] || [[ "$INTERVAL_DAYS" -lt 0 ]]; then
  echo "ERREUR: L'intervalle doit être un nombre positif de jours" >&2
  exit 1
fi

# Convertir en secondes
INTERVAL=$(( INTERVAL_DAYS * 24 * 60 * 60 ))

# Arret propre du conteneur
trap "echo 'Arrêt du conteneur'; exit 0" SIGTERM SIGINT

# Exécuter immédiatement puis planifier
echo "=== Démarrage initial ==="
./scripts/update.sh

# Boucle principale pour les exécutions périodiques
while [[ "$INTERVAL" -gt 0 ]]; do
  echo "=== Prochaine exécution dans $INTERVAL_DAYS jours ==="
  sleep "$INTERVAL"
  echo "=== Démarrage planifié ==="
  ./scripts/update.sh
done
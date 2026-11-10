#!/bin/sh
set -e

echo "[ENTRYPOINT] Lancement de l'environnement conteneurisé Kolix..."

# Exécution via Python
exec python /app/scripts/entrypoint.py "$@"


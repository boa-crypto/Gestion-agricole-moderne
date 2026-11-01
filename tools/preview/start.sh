#!/bin/bash
# Aperçu AgriPro : front sur 3000 (seule origine exposée), backend sur 8500.
# Le serveur de développement relaie /_event vers le backend (voir
# patch_vite_template.py) : le navigateur distant n'a qu'un seul hôte à joindre.
set -euo pipefail
REPO=/home/user/Gestion-agricole-moderne
ROOT=${PREVIEW_ROOT:-/tmp/preview}
FRONT=${PREVIEW_FRONTEND_PORT:-3000}
BACK=${PREVIEW_BACKEND_PORT:-8500}
export AGRI_PRO_PREVIEW_AUTH_DB=${AGRI_PRO_PREVIEW_AUTH_DB:-$REPO/.preview/data/preview_auth.db}
cd "$ROOT"
CI=1 AGRI_PRO_PREVIEW_STUB=1 AGRI_PRO_PREVIEW_BACKEND="$BACK" REFLEX_USE_NPM=1 \
  "$REPO/.venv/bin/reflex" run --env dev \
  --frontend-port "$FRONT" --backend-port "$BACK"

#!/bin/bash
# Reconstruit entièrement l'aperçu : environnement, copie, correctifs, données.
# Utilisable après chaque redémarrage du bac à sable ; idempotent pour l'essentiel.
set -euo pipefail
REPO=/home/user/Gestion-agricole-moderne
ROOT=${PREVIEW_ROOT:-/tmp/preview}
export AGRI_PRO_PREVIEW_STUB=1
export PREVIEW_ROOT="$ROOT"
cd "$REPO"

if [ ! -x .venv/bin/python ]; then
  echo "== environnement Python =="
  python3 -m venv .venv
  .venv/bin/python -m pip install -q --upgrade pip
  .venv/bin/python -m pip install -q -r requirements.txt brotli
fi

echo "== copie d'aperçu =="
rm -rf "$ROOT"
mkdir -p "$ROOT"
tar -cf - --exclude=.git --exclude=.venv --exclude=.web --exclude=node_modules \
  --exclude=.states --exclude=__pycache__ --exclude=.preview . 2>/dev/null \
  | (cd "$ROOT" && tar -xf -)

echo "== correctifs =="
.venv/bin/python tools/preview/patch_preview.py
.venv/bin/python tools/preview/patch_vite_template.py

echo "== données de démonstration =="
.venv/bin/python tools/preview/warm.py "$ROOT"

echo "== compte de démonstration =="
.venv/bin/python tools/preview/seed_account.py "$ROOT"

echo "== prêt : lancer tools/preview/start.sh =="

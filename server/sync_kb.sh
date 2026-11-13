#!/bin/bash
# Copie les documents du projet vers le dossier indexe par la base de connaissances.
# Usage : server/sync_kb.sh   (KB_DIR pour changer la destination)
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${KB_DIR:-/home/debian/kb/perso/girls-ai}"
git -C "$REPO" pull -q --ff-only || echo "sync_kb: git pull a echoue, copie de la version locale" >&2
mkdir -p "$DEST"
for f in journal-projet automation-architecture compliance accounts-setup; do
  cp "$REPO/docs/$f.md" "$DEST/$f.md"
done
echo "sync_kb: $(ls "$DEST" | wc -l) fichiers dans $DEST"

#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT/hosting/public/static"
cp "$ROOT/backend/app/static/"* "$ROOT/hosting/public/static/"
cp "$ROOT/backend/app/static/index.html" "$ROOT/hosting/public/index.html"
if [[ -f "$ROOT/hosting/public/firebase-config.local.js" ]]; then
  cp "$ROOT/hosting/public/firebase-config.local.js" "$ROOT/hosting/public/firebase-config.js"
fi
echo "Hosting assets prepared in hosting/public/"

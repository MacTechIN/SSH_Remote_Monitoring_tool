#!/usr/bin/env bash
# Hosting만 먼저 배포 (Cloud Run 없이도 Site Not Found 해결)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PROJECT_ID="${FIREBASE_PROJECT_ID:-ssh-analyzer}"

if [[ -z "${FIREBASE_TOKEN:-}" ]]; then
  echo "FIREBASE_TOKEN이 없으면: firebase login 후 firebase login:ci 로 토큰 발급" >&2
  echo "  export FIREBASE_TOKEN=..." >&2
  exit 1
fi

bash scripts/prepare-hosting.sh
npm install -g firebase-tools

echo "==> Deploy Hosting only (no /api rewrite to Cloud Run)"
firebase deploy --only hosting --project "$PROJECT_ID" --config firebase.hosting-only.json --non-interactive

echo "Open: https://${PROJECT_ID}.web.app"
echo "Note: /api 는 Cloud Run 배포 후 firebase.json 전체 배포가 필요합니다."

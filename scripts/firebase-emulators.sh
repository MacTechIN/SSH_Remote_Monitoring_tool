#!/usr/bin/env bash
# Firebase 로컬 에뮬레이터 (Functions + Firestore + Hosting)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .firebaserc ]]; then
  echo "⚠️  .firebaserc 없음 — 데모 프로젝트로 생성합니다."
  echo '{"projects":{"default":"demo-ssh-monitor"}}' > .firebaserc
fi

if [[ ! -f functions/.env ]]; then
  echo "→ functions/.env.example → functions/.env"
  cp functions/.env.example functions/.env
fi

if [[ ! -d functions/venv ]]; then
  echo "→ functions Python venv 생성 (python3.12 -m venv venv)"
  python3.12 -m venv functions/venv
  functions/venv/bin/pip install -r functions/requirements.txt
fi

if [[ ! -d web/out ]]; then
  echo "→ web Firebase 빌드"
  npm run web:build:firebase
fi

export FIRESTORE_EMULATOR_HOST="${FIRESTORE_EMULATOR_HOST:-127.0.0.1:8080}"
export FIREBASE_AUTH_EMULATOR_HOST="${FIREBASE_AUTH_EMULATOR_HOST:-127.0.0.1:9099}"
export FUNCTIONS_EMULATOR="${FUNCTIONS_EMULATOR:-true}"

echo "에뮬레이터 UI: http://localhost:4000"
echo "Hosting:       http://localhost:5000"
echo "Functions:     http://localhost:5001"
exec npx firebase emulators:start --import=.firebase-emulator-data --export-on-exit

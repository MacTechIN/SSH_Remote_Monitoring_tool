#!/usr/bin/env bash
# Firebase Hosting + Firestore rules + Cloud Run API 배포
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PROJECT_ID="${FIREBASE_PROJECT_ID:-}"
REGION="${CLOUD_RUN_REGION:-asia-northeast3}"
SERVICE_NAME="${CLOUD_RUN_SERVICE:-ssh-monitor-api}"

if [[ -z "$PROJECT_ID" ]]; then
  if [[ -f .firebaserc ]]; then
    PROJECT_ID="$(python3 -c "import json; print(json.load(open('.firebaserc'))['projects']['default'])")"
  fi
fi
if [[ -z "$PROJECT_ID" || "$PROJECT_ID" == "YOUR_FIREBASE_PROJECT_ID" ]]; then
  echo "FIREBASE_PROJECT_ID 또는 .firebaserc 를 설정하세요." >&2
  exit 1
fi

echo "==> Prepare hosting static"
bash scripts/prepare-hosting.sh

SECRET_ARGS=()
if gcloud secrets describe ssh-monitor-key --project "$PROJECT_ID" >/dev/null 2>&1; then
  SECRET_ARGS=(--set-secrets "SSH_PRIVATE_KEY=ssh-monitor-key:latest")
fi

echo "==> Deploy Cloud Run API ($SERVICE_NAME)"
gcloud config set project "$PROJECT_ID"
gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "STORAGE_BACKEND=firestore,FIREBASE_AUTH_REQUIRED=true,HISTORY_ENABLED=true" \
  "${SECRET_ARGS[@]}" \
  --min-instances 0 \
  --max-instances 3 \
  --memory 512Mi \
  --timeout 120

echo "==> Deploy Firebase (Hosting + Firestore rules)"
firebase deploy --only hosting,firestore --project "$PROJECT_ID"

echo "Done. Open: https://${PROJECT_ID}.web.app"

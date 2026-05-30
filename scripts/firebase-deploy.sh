#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .firebaserc ]]; then
  echo "오류: .firebaserc 가 없습니다. cp .firebaserc.example .firebaserc 후 프로젝트 ID를 설정하세요."
  exit 1
fi

echo "→ Web build (Firebase Hosting)"
npm run web:build:firebase

echo "→ Firestore rules & indexes"
npx firebase deploy --only firestore

echo "→ Cloud Functions (api, scheduled_poll)"
npx firebase deploy --only functions

echo "→ Hosting"
npx firebase deploy --only hosting

echo "완료: firebase hosting:channel:list 또는 Firebase Console에서 URL 확인"

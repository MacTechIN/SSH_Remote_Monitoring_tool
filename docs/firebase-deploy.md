# Firebase 프로덕션 배포 가이드

SSH Remote Monitoring을 **Firebase Hosting + Firestore + Cloud Run**으로 운영하는 방법입니다.

## 아키텍처

| 구성 요소 | 역할 |
|-----------|------|
| **Firebase Hosting** | 대시보드 정적 파일 (`hosting/public`) |
| **Cloud Run** | FastAPI API + SSH 메트릭 수집 (`ssh-monitor-api`) |
| **Firestore** | 호스트 설정·메트릭 히스토리 |
| **Firebase Authentication** | 사용자 로그인 (이메일/비밀번호 등) |
| **Secret Manager** | SSH 개인키 (`ssh-monitor-key`) |

Hosting의 `/api/**` 요청은 `firebase.json` rewrite로 Cloud Run으로 전달됩니다.

## 1. 사전 준비

1. [Firebase Console](https://console.firebase.google.com/)에서 프로젝트 생성
2. Authentication → Sign-in method 활성화 (Email/Password 권장)
3. Firestore Database 생성 (production mode)
4. [Google Cloud Console](https://console.cloud.google.com/)에서 결제 활성화
5. 로컬 도구 설치:

```bash
npm install
gcloud auth login
firebase login
```

## 2. 프로젝트 연결

```bash
cp .firebaserc.example .firebaserc
# default 프로젝트 ID 수정

firebase use YOUR_PROJECT_ID
gcloud config set project YOUR_PROJECT_ID
```

## 3. SSH 키 (Secret Manager)

```bash
gcloud secrets create ssh-monitor-key --replication-policy=automatic
gcloud secrets versions add ssh-monitor-key --data-file=$HOME/.ssh/id_ed25519
```

Cloud Run 서비스 계정에 `roles/secretmanager.secretAccessor` 권한을 부여하세요.

배포 스크립트는 `SSH_PRIVATE_KEY` 환경 변수로 시크릿을 마운트합니다. 앱은 `SSH_PRIVATE_KEY_PATH` 또는 시크릿 파일 경로를 사용합니다.

## 4. Firebase 웹 설정

Hosting용 `firebase-config.js` 생성:

```bash
# Console > 프로젝트 설정 > 일반 > 내 앱 > 웹 앱 SDK 구성 복사
cat > hosting/public/firebase-config.local.js <<'EOF'
window.__FIREBASE_CONFIG__ = {
  apiKey: "...",
  authDomain: "...",
  projectId: "...",
  storageBucket: "...",
  messagingSenderId: "...",
  appId: "..."
};
window.__FIREBASE_AUTH_ENABLED__ = true;
EOF

bash scripts/prepare-hosting.sh
```

## 5. 배포

```bash
export FIREBASE_PROJECT_ID=YOUR_PROJECT_ID
bash scripts/firebase-deploy.sh
```

또는:

```bash
npm run firebase:deploy
```

## 6. 로컬 에뮬레이터 (선택)

터미널 1 — API:

```bash
export STORAGE_BACKEND=file
export FIRESTORE_EMULATOR_HOST=localhost:8085
make run
```

터미널 2:

```bash
firebase emulators:start
```

## 환경 변수 (Cloud Run)

| 변수 | 값 |
|------|-----|
| `STORAGE_BACKEND` | `firestore` |
| `FIREBASE_AUTH_REQUIRED` | `true` |
| `HISTORY_ENABLED` | `true` |
| `CORS_ORIGINS` | Hosting URL |

## 보안 참고

- Firestore 규칙은 클라이언트 직접 접근을 차단합니다 (`firestore.rules`).
- API는 Firebase ID 토큰으로 보호합니다 (`FIREBASE_AUTH_REQUIRED=true`).
- SSH 개인키는 Firestore에 저장하지 마세요.

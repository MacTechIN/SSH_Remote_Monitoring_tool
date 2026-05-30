# Firebase 배포 가이드

Docker 스택(PostgreSQL + Celery + Redis)과 **별도**로, Firebase만으로 운영하는 경로입니다.

## 아키텍처 비교

| 구성 | Docker | Firebase |
|------|--------|----------|
| 웹 | Next.js 컨테이너 | **Firebase Hosting** (`web/out`) |
| API | FastAPI 컨테이너 | **Cloud Functions** (`functions/api`) |
| DB | PostgreSQL + TimescaleDB | **Firestore** |
| 스케줄 수집 | Celery Beat + Worker | **scheduled_poll** (1분마다) |
| 실시간 | WebSocket + Redis | **15초 폴링** (Hosting 제한) |

Docker 디렉터리·`docker-compose.yml`은 그대로 두고, Firebase용 파일은 루트 `firebase.json`, `functions/` 에 있습니다.

## 사전 요구

1. [Firebase CLI](https://firebase.google.com/docs/cli) — `npm i -g firebase-tools` 또는 루트 `npm install`
2. Firebase 프로젝트 생성 (Blaze 요금제 — Cloud Functions 외부 SSH 필요)
3. `cp .firebaserc.example .firebaserc` 후 프로젝트 ID 설정

## 시크릿 설정

```bash
firebase login
firebase use YOUR_PROJECT_ID

firebase functions:secrets:set ENCRYPTION_KEY
firebase functions:secrets:set JWT_SECRET
firebase functions:secrets:set ADMIN_USERNAME
firebase functions:secrets:set ADMIN_PASSWORD
```

`ENCRYPTION_KEY` 생성:

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Functions에 시크릿 바인딩은 `functions/main.py` 배포 시 Firebase가 환경 변수로 주입합니다.  
로컬 에뮬레이터용: `functions/.env` (gitignore)에 동일 키 설정.

## 로컬 에뮬레이터

```bash
# 터미널 1 — API + Firestore 에뮬레이터
export ENCRYPTION_KEY=your-fernet-key
export JWT_SECRET=your-jwt-secret
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=admin
firebase emulators:start

# 터미널 2 — 웹 (에뮬레이터 Hosting 5000, Functions 5001)
cd web && npm run build:firebase
# hosting은 emulators가 web/out 을 서빙
```

에뮬레이터 UI: http://localhost:4000

## 프로덕션 배포

```bash
# 루트에서
npm install
npm run firebase:deploy
```

단계별:

```bash
npm run web:build:firebase          # web/out 생성
firebase deploy --only firestore    # 규칙·인덱스
firebase deploy --only functions    # api + scheduled_poll
firebase deploy --only hosting      # 정적 웹 + /api rewrite
```

배포 후 URL: `https://YOUR_PROJECT_ID.web.app`

## API 경로

Hosting rewrite로 **동일 출처** 호출:

- `POST /api/v1/auth/login`
- `/api/v1/hosts`, `/api/v1/activity/*`, `/api/v1/search/*`

웹 빌드 시 `NEXT_PUBLIC_DEPLOY_TARGET=firebase`, `NEXT_PUBLIC_API_URL=` (빈 문자열) 사용.

## SSH 호스트 등록

Docker 버전과 동일하게 **호스트** 화면에서 PEM 키 등록.  
Functions가 `asyncssh`로 원격 서버에 접속합니다. 방화벽에서 Google Cloud Functions IP 허용이 필요할 수 있습니다.

## 제한 사항

- WebSocket 실시간 대시보드는 Firebase Hosting에서 미지원 → 15초 간격 REST 폴링
- `scheduled_poll` 최소 간격 1분 (Cloud Scheduler)
- Firestore는 Timescale hypertable 대신 문서 저장 (대용량 시 비용·쿼리 설계 필요)

## 문제 해결

| 증상 | 조치 |
|------|------|
| 401 로그인 실패 | Functions 시크릿 `ADMIN_*` 확인 |
| 수집 실패 | `ENCRYPTION_KEY`가 Docker와 동일 Fernet 형식인지 확인 |
| CORS | `functions/config.py` `CORS_ORIGINS` 또는 Hosting 동일 출처 |
| 인덱스 오류 | `firebase deploy --only firestore:indexes` |

## 관련 파일

- `firebase.json` — Hosting + Functions + Firestore
- `functions/` — FastAPI(Firestore) + 스케줄러
- `firestore.rules` — 클라이언트 직접 접근 차단
- `.env.firebase.example` — 환경 변수 안내

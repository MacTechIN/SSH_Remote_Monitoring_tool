# Implement — SSH 원격 프로세스 모니터링 (옵션 A)

> **전제:** `research.md`, `plan.md` 승인  
> **상태:** 구현 대기 · **스택:** FastAPI + Celery + TimescaleDB + Next.js

---

## 게이트 0 — 문서 승인

- [x] `research.md` (옵션 A) 검토 완료
- [x] `plan.md` 검토 완료
- [x] 본 `implement.md` 착수 승인

---

## 1. 저장소 초기화

### 1.1 Python 백엔드

- [x] `backend/pyproject.toml` — fastapi, uvicorn, sqlalchemy, alembic, asyncssh, celery, redis, cryptography, pydantic-settings
- [x] `backend/app/main.py` — FastAPI 앱, CORS, 라우터 등록
- [x] `backend/app/core/config.py` — Settings
- [x] dev: `uvicorn app.main:app --reload`

### 1.2 Celery

- [x] `backend/app/worker/celery_app.py`
- [x] `backend/app/worker/tasks.py` — poll_host, build_daily_rollup
- [x] Beat 스케줄 설정

### 1.3 프론트엔드

- [x] `web/` — Next.js App Router
- [x] `NEXT_PUBLIC_API_URL` 환경 변수

### 1.5 Figma 대체 스캐폴드 (선행·문서화됨)

- [x] `web/src/design-tokens/` — tokens.json, tokens.css, figma-map.json, index.ts
- [x] `web/src/components/ui/` — Button, Badge, ui-primitives.css
- [x] `web/src/components/layouts/AppShell` + CSS
- [x] `web/src/components/features/ActivityHeatmap/` — View, types, Container.example
- [x] `web/tailwind.preset.ts`, `scripts/sync-tokens-from-figma.mjs`
- [x] `docs/design-system.md`, `web/DESIGN_HANDOFF.md`
- [x] Next.js `tsconfig` paths `@/*`, globals.css `@import` 토큰·CSS
- [x] `package.json` script: `tokens:sync`
- [ ] Figma 파일 URL을 `DESIGN_HANDOFF.md`에 기입

### 1.4 품질

- [x] ruff + pytest + pytest-asyncio
- [ ] `pre-commit` (선택)

**게이트 1:** `pip install` / `uv sync` 성공, `uvicorn` 기동

---

## 2. 인프라

### 2.1 Docker Compose

- [x] `timescale/timescaledb:latest-pg16`
- [x] `redis:7`
- [x] 서비스: `api`, `worker`, `beat`, `web`
- [x] healthcheck

### 2.2 Alembic + Timescale

- [x] 초기 스키마: hosts, snapshots, processes, sessions, rollups, rules, audit
- [x] `CREATE EXTENSION IF NOT EXISTS timescaledb`
- [x] `create_hypertable('process_snapshots', 'collected_at')`
- [x] 시드: system allowlist 규칙

### 2.3 환경

- [x] `.env.example`
- [x] `ENCRYPTION_KEY` 생성 방법 (Fernet)

**게이트 2:** `docker compose up` — DB·Redis healthy

---

## 3. SSH·수집

- [x] `SshService` — asyncssh connect, run, disconnect
- [x] known_hosts 검증 (MVP: known_hosts=None, 프로덕션 강화 예정)
- [x] `parse_ps`, `parse_who` + fixture 테스트
- [x] `ClassificationService`
- [x] `CollectorService` — DB commit + Redis WS publish

**게이트 3:** CLI/태스크로 1호스트 수집 → DB 확인

---

## 4. Celery·집계

- [x] `poll_host.delay(host_id)` 동작
- [x] Host enable 시 Beat 스케줄 등록/갱신
- [ ] Host disable 시 스케줄 제거
- [x] `build_daily_rollup` — 시간대 0–23 집계
- [ ] `SSH_MAX_CONCURRENT` 세마포어 (asyncio)

**게이트 4:** 2분 자동 폴링 + rollup row

---

## 5. FastAPI

- [x] Host router + test-connection + collect
- [x] Activity router (calendar, day-summary)
- [x] Search router
- [x] WebSocket `/ws/v1/live`
- [x] JWT login (admin MVP)
- [x] OpenAPI `/docs` 확인

**게이트 5:** curl/httpx로 API 계약 검증

---

## 6. Next.js

### 6.0 Figma 연동 (페이지 구현 시)

- [x] 모든 페이지: `page.tsx` → `*Container` → `*View`만 렌더
- [x] 스타일은 tokens / ui primitives / View 내부만 (Container 무스타일)
- [x] Heatmap·차트 색: `getActivityColor()` / CSS 변수
- [x] `/design-preview` — ui primitives + tokens 시각 검증

### 6.1 기능 페이지

- [x] `DashboardContainer` + `DashboardView` + WebSocket hook
- [x] `/activity` — `ActivityHeatmapContainer` + View + day-summary tooltip
- [ ] `/activity/[date]` Recharts 24h (token colors)
- [x] `HostsContainer` + `HostsView`, `SearchContainer`
- [x] classification — `Badge` primitive (Figma 교체 대상)

**게이트 6:** 브라우저 E2E 수동 확인

### 6.2 Figma 디자인 수령 후 (교체 단계)

- [ ] Variables export → `npm run tokens:sync`
- [ ] `components/ui/*` Figma 컴포넌트로 교체
- [ ] `*View.tsx` 레이아웃 Figma 스펙 반영
- [ ] Container·hooks diff 없음 확인
- [ ] `figma/code-connect/*.figma.tsx` (선택)

---

## 7. CI/CD

- [x] `.github/workflows/ci.yml` — ruff, pytest, web build
- [x] Docker Compose 정의
- [x] README 배포 절차

**게이트 7:** CI green

---

## 8. 보안 (출시 전)

- [ ] 시크릿 Git 미포함
- [ ] CORS production
- [ ] (선택) slowapi rate limit

---

## 9. Definition of Done

1. 60초 주기 스냅샷 적재 (Timescale hypertable)
2. 대시보드 WebSocket 실시간 갱신
3. 일/주/월/년 heatmap + hover 일별 요약
4. 기간·사용자·명령 검색
5. `docker compose up` + CI 통과
6. UI가 **View/Container + design tokens** 구조를 따름 (Figma 교체 가능)

---

## 10. 구현 순서

```
backend scaffold → Docker/Timescale/Alembic → SSH/Parser/Collector
→ Celery tasks → FastAPI REST/WS → Next.js → CI
```

---

## 11. 진행 로그

| 날짜 | 게이트 | 확인 | 비고 |
|------|--------|------|------|
| | 0 | | 옵션 A로 전환 |
| | 1–7 | | |

---

---

## 12. Firebase 배포 (Docker와 병행)

- [x] `firebase.json` — Hosting + Functions + Firestore
- [x] `functions/` — FastAPI(Firestore) + `scheduled_poll`
- [x] `web` — `npm run build:firebase` (static export)
- [x] [docs/firebase-deploy.md](./docs/firebase-deploy.md)
- [ ] 프로덕션 Firebase 프로젝트 ID·시크릿 설정 (운영자)
- [ ] `firebase deploy` 검증

**다음 액션:** Docker는 `docker compose up`, Firebase는 `docs/firebase-deploy.md` 참고.

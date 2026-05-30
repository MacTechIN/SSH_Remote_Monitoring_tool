# Implement — SSH 원격 프로세스 모니터링 (옵션 A)

> **전제:** `research.md`, `plan.md` 승인  
> **상태:** 구현 대기 · **스택:** FastAPI + Celery + TimescaleDB + Next.js

---

## 게이트 0 — 문서 승인

- [ ] `research.md` (옵션 A) 검토 완료
- [ ] `plan.md` 검토 완료
- [ ] 본 `implement.md` 착수 승인

---

## 1. 저장소 초기화

### 1.1 Python 백엔드

- [ ] `backend/pyproject.toml` — fastapi, uvicorn, sqlalchemy, alembic, asyncssh, celery, redis, cryptography, pydantic-settings
- [ ] `backend/app/main.py` — FastAPI 앱, CORS, 라우터 등록
- [ ] `backend/app/core/config.py` — Settings
- [ ] dev: `uvicorn app.main:app --reload`

### 1.2 Celery

- [ ] `backend/app/worker/celery_app.py`
- [ ] `backend/app/worker/tasks.py` — poll_host, build_daily_rollup
- [ ] Beat 스케줄 설정

### 1.3 프론트엔드

- [ ] `web/` — Next.js App Router + Tailwind
- [ ] `NEXT_PUBLIC_API_URL` 환경 변수

### 1.4 품질

- [ ] ruff + pytest + pytest-asyncio
- [ ] `pre-commit` (선택)

**게이트 1:** `pip install` / `uv sync` 성공, `uvicorn` 기동

---

## 2. 인프라

### 2.1 Docker Compose

- [ ] `timescale/timescaledb:latest-pg16`
- [ ] `redis:7`
- [ ] 서비스: `api`, `worker`, `beat`, `web`
- [ ] healthcheck

### 2.2 Alembic + Timescale

- [ ] 초기 스키마: hosts, snapshots, processes, sessions, rollups, rules, audit
- [ ] `CREATE EXTENSION IF NOT EXISTS timescaledb`
- [ ] `create_hypertable('process_snapshots', 'collected_at')`
- [ ] 시드: system allowlist 규칙

### 2.3 환경

- [ ] `.env.example`
- [ ] `ENCRYPTION_KEY` 생성 방법 (Fernet)

**게이트 2:** `docker compose up` — DB·Redis healthy

---

## 3. SSH·수집

- [ ] `SshService` — asyncssh connect, run, disconnect
- [ ] known_hosts 검증
- [ ] `parse_ps`, `parse_who` + fixture 테스트
- [ ] `ClassificationService`
- [ ] `CollectorService` — DB commit + WS publish hook

**게이트 3:** CLI/태스크로 1호스트 수집 → DB 확인

---

## 4. Celery·집계

- [ ] `poll_host.delay(host_id)` 동작
- [ ] Host enable 시 Beat 스케줄 등록/갱신
- [ ] Host disable 시 스케줄 제거
- [ ] `build_daily_rollup` — 시간대 0–23 집계
- [ ] `SSH_MAX_CONCURRENT` 세마포어 (asyncio)

**게이트 4:** 2분 자동 폴링 + rollup row

---

## 5. FastAPI

- [ ] Host router + test-connection
- [ ] Activity router (calendar, day-summary)
- [ ] Search router
- [ ] WebSocket `/ws/v1/live`
- [ ] JWT login (admin MVP)
- [ ] OpenAPI `/docs` 확인

**게이트 5:** curl/httpx로 API 계약 검증

---

## 6. Next.js

- [ ] 대시보드 + WebSocket hook
- [ ] `/activity` heatmap + tooltip (day-summary)
- [ ] `/activity/[date]` Recharts 24h
- [ ] `/hosts`, `/search`
- [ ] system/user 뱃지 UI

**게이트 6:** 브라우저 E2E 수동 확인

---

## 7. CI/CD

- [ ] `.github/workflows/ci.yml` — ruff, pytest, alembic check
- [ ] Docker build on push
- [ ] README 배포 절차

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

**다음 액션:** 게이트 0–2 승인 → `backend/` + Docker + Alembic 구현 착수.

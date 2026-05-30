# SSH Remote Monitoring Tool

원격 Linux 호스트에 SSH로 프로세스·세션을 수집하고, 시스템/사용자 프로세스를 분류해 웹 대시보드와 GitHub 스타일 활동 캘린더로 보여 주는 도구입니다.

## 스택

- **Backend:** FastAPI, Celery, Redis, SQLAlchemy, Alembic, asyncssh
- **DB:** PostgreSQL + TimescaleDB
- **Web:** Next.js 15 (View/Container + design tokens, Figma 대체 준비)

## 빠른 시작

```bash
cp .env.example .env
docker compose up --build
```

| 서비스 | URL |
|--------|-----|
| API | http://localhost:8000/docs |
| Web | http://localhost:3000 |
| 로그인 | `admin` / `admin` (`.env`에서 변경) |

### 로컬 개발 (Docker 없이)

```bash
# DB·Redis는 docker compose up db redis 만 실행
cd backend && pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload

# 다른 터미널
celery -A app.worker.celery_app worker -l info
celery -A app.worker.celery_app beat -l info

cd web && npm install && npm run dev
```

## 문서

- [research.md](./research.md) · [plan.md](./plan.md) · [implement.md](./implement.md)
- [docs/design-system.md](./docs/design-system.md) — Figma UI 교체 규칙
- [web/DESIGN_HANDOFF.md](./web/DESIGN_HANDOFF.md)

## 주요 API

- `POST /api/v1/auth/login`
- `CRUD /api/v1/hosts` · `POST .../test-connection` · `POST .../collect`
- `GET /api/v1/activity/calendar` · `day-summary`
- `GET /api/v1/search/processes`
- `WS /ws/v1/live?host_id=`

## Figma 디자인 반영

1. `web/src/design-tokens/` 갱신  
2. `web/src/components/ui/` 교체  
3. `*View.tsx` 레이아웃만 수정 (Container·API 유지)

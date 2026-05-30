# Research — SSH 원격 프로세스 모니터링 (옵션 A)

> **상태:** 초안 · **선택 스택:** 옵션 A (Python 중심)  
> **다음 단계:** 본 문서 검토·승인 후 `plan.md` 확정

---

## 1. 프로젝트 목표 요약

| 목표 | 설명 |
|------|------|
| 원격 수집 | SSH로 접속한 서버에서 프로세스·세션 정보 수집 |
| 분류 | OS/시스템 기본 프로세스 vs 사용자가 기동한 프로세스 구분 |
| 실시간 모니터링 | 현재 어떤 사용자가 어떤 작업(프로세스) 중인지 웹에서 확인 |
| 영속 기록 | 시간별 스냅샷을 DB에 저장, 과거 검색·필터 |
| 활동 캘린더 | GitHub contributions 스타일 heatmap (일/주/월/년, 시간대별) |
| Hover 요약 | 날짜 셀에 커서를 올리면 해당일 사용자·프로세스·지속 시간 요약 표시 |
| 배포 | Git 저장소 기반 CI/CD로 웹앱 배포 |

---

## 2. 스택 결정 — 옵션 A

**옵션 B(Node.js)** 에서 **옵션 A(Python)** 로 변경함. 아래 구성으로 일원화한다.

| 계층 | 기술 | 버전 가이드 (2026 기준) |
|------|------|-------------------------|
| API | **FastAPI** | 0.115+ |
| 언어 | **Python** | 3.12+ |
| SSH | **asyncssh** (비동기 우선) 또는 Paramiko (동기 fallback) | 최신 안정 |
| 작업 큐·스케줄 | **Celery** + **Redis** (broker/backend) | Celery 5.x |
| 주기 작업 | Celery Beat (호스트별 폴링 스케줄) | — |
| ORM | **SQLAlchemy 2.x** + **Alembic** | — |
| DB | **PostgreSQL 16+** + **TimescaleDB** (시계열·집계) | — |
| 실시간 | FastAPI **WebSocket** (또는 SSE) | — |
| 프론트엔드 | **Next.js** (App Router) | 15.x |
| UI·차트 | Tailwind CSS, **react-calendar-heatmap**, **Recharts** | — |
| 설정 | **pydantic-settings** | — |
| 컨테이너 | Docker Compose (api, worker, beat, redis, postgres, web) | — |
| CI/CD | **GitHub Actions** (pytest, ruff, docker build) | — |

### 옵션 A를 선택한 근거

1. **MVP 속도**: 프로세스 파싱·분류 규칙을 스크립트처럼 빠르게 반복 가능.
2. **모니터링 생태계**: ps 출력 파싱, 데이터 파이프라인·배치에 Python 라이브러리가 풍부.
3. **시계열 DB**: TimescaleDB와 SQLAlchemy/Alembic 조합이 스냅샷·rollup에 적합.
4. **비동기 SSH**: asyncssh + FastAPI async로 다수 호스트 폴링 시 I/O 효율.
5. **운영 친화**: Celery Beat로 호스트별 주기 작업 관리가 단순.

### 옵션 B 대비 변경 요약

| 항목 | 옵션 B (이전) | 옵션 A (현재) |
|------|---------------|---------------|
| API | NestJS | FastAPI |
| 큐 | BullMQ | Celery + Redis |
| ORM | Prisma | SQLAlchemy + Alembic |
| DB | PostgreSQL | PostgreSQL + **TimescaleDB** |
| SSH | ssh2 | **asyncssh** |
| 실시간 | Socket.io | FastAPI WebSocket |
| 프론트 | Next.js | Next.js (동일) |

---

## 3. 수집 아키텍처

### 3.1 권장 모델: 중앙 Pull (Phase 1)

```
┌──────────────┐     SSH       ┌──────────────────┐
│ Celery Worker│ ────────────► │ Remote Linux Host │
│ (asyncssh)   │   ps/who/w    │                  │
└──────┬───────┘               └──────────────────┘
       │ INSERT hypertable
       ▼
┌──────────────┐     WS/SSE    ┌─────────────┐
│ PostgreSQL   │ ◄──────────── │ FastAPI     │ ◄── Next.js
│ + TimescaleDB│               └─────────────┘
└──────────────┘
```

- Phase 1: 중앙 서버가 등록 호스트에 주기적으로 SSH 접속 (에이전트 없음).
- Phase 2: 필요 시 경량 Push 에이전트 검토.

### 3.2 SSH에서 실행할 명령 (초기 세트)

| 명령 | 용도 |
|------|------|
| `ps -eo pid,ppid,user:32,comm,cmd,%cpu,%mem,etime --sort=-%cpu` | 프로세스 목록 |
| `who -u` / `w -h` | 로그인 세션 |
| `id -u <user>` (필요 시) | UID 확인 |

### 3.3 프로세스 분류 규칙 (초안)

| 분류 | 조건 예시 |
|------|-----------|
| `system` | UID 0 + allowlist (sshd, systemd, cron, …) |
| `system` | PPID=1 및 데몬 allowlist |
| `user` | UID ≥ 1000 (설정 가능 `min_uid`) |
| `user` | 로그인 세션 TTY와 연관된 프로세스 트리 |
| `unknown` | 미매칭 — 규칙 DB에서 추후 조정 |

규칙 테이블 `classification_rules`로 코드 배포 없이 변경.

### 3.4 보안

- SSH **개인키**만 사용.
- 키는 DB **암호화 at rest** (Fernet 또는 AES-GCM, `ENCRYPTION_KEY`).
- `known_hosts` 검증 필수.
- 감사 로그: `audit_events` 테이블.

---

## 4. 데이터 모델 (개념)

### 4.1 핵심 엔티티

- **Host** — 연결 정보, 암호화 키, `poll_interval_sec`
- **ProcessSnapshot** — `collected_at`, `host_id`, `parser_version` (Timescale **hypertable** 후보)
- **ProcessRecord** — pid, user, comm, cmd, classification
- **UserSession** — user, tty, idle, from_ip
- **DailyActivityRollup** — date, hour(0–23), user, event_count, `summary_json` (heatmap tooltip)
- **ClassificationRule**, **AuditEvent**

### 4.2 TimescaleDB 활용

- `process_snapshots`: `collected_at` 기준 hypertable → 시간 범위 쿼리·보존 정책.
- **Continuous aggregate** (선택): 시간대별 rollup 자동 갱신.
- 오래된 raw JSON: retention policy (예: 90일) — Phase 2.

### 4.3 인덱스

- `(host_id, collected_at DESC)`
- `(host_id, user, date)` on rollup — 캘린더 API

---

## 5. API·실시간 설계 (요약)

| 용도 | 방식 |
|------|------|
| CRUD·검색 | REST `/api/v1/...` |
| 라이브 상태 | WebSocket `/ws/v1/live?host_id=` |
| Heatmap | `GET /api/v1/activity/calendar` |
| Hover | `GET /api/v1/activity/day-summary?date=` |

OpenAPI는 FastAPI 자동 문서 (`/docs`).

---

## 6. 프론트엔드 UI

- **react-calendar-heatmap**: GitHub 스타일 주 단위 그리드 + tooltip.
- **Recharts**: 일별 24시간 drill-down.
- 화면: 대시보드, 활동 캘린더, 호스트 관리, 검색 (plan.md와 동일).

### 6.1 Figma 디자인 대체 준비 (추가)

추후 Figma에서 완성된 UI로 **스타일·레이아웃만 교체**할 수 있도록 다음을 채택한다.

| 원칙 | 설명 |
|------|------|
| **Design Tokens** | Figma Variables → `tokens.json` / `tokens.css` / `figma-map.json` |
| **UI / Feature 분리** | `components/ui` = Figma 1:1, `features/*View` = Presentational, `*Container` = API·WS |
| **토큰 단일 소스** | hex 하드코딩 금지; heatmap 색은 `--activity-0`…`4` |
| **Code Connect** | `web/figma/code-connect/*.figma.tsx` (선택) |
| **동기화 스크립트** | `scripts/sync-tokens-from-figma.mjs` 스켈레톤 |

상세: [docs/design-system.md](./docs/design-system.md), 스캐폴드: [web/](./web/)

---

## 7. Celery 작업 설계

| Task | 설명 |
|------|------|
| `tasks.poll_host` | 단일 호스트 SSH 수집 |
| `tasks.build_daily_rollup` | 스냅샷 → 시간대 집계 |
| Beat | 호스트별 `poll_interval`마다 `poll_host` 스케줄 |

- `CELERY_WORKER_CONCURRENCY`, `SSH_MAX_CONCURRENT=10` 환경 변수.
- 실패: retry + exponential backoff (max 3).

---

## 8. 저장소 구조 (권장)

```
/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routers
│   │   ├── core/         # config, security
│   │   ├── models/       # SQLAlchemy
│   │   ├── services/     # ssh, parser, classifier, collector
│   │   └── schemas/      # Pydantic
│   ├── alembic/
│   └── tests/
├── worker/
│   └── celery_app.py     # tasks (또는 backend/app/worker)
├── web/                  # Next.js
│   ├── src/design-tokens/
│   ├── src/components/ui/       # Figma primitives
│   ├── src/components/features/ # View + Container
│   └── figma/code-connect/
├── docs/design-system.md
├── docker-compose.yml
└── .github/workflows/
```

---

## 9. 대안·리스크

| 리스크 | 완화 |
|--------|------|
| TimescaleDB 운영 학습 | Docker 이미지 `timescale/timescaledb`로 로컬·프로덕션 통일 |
| OS별 `ps` 차이 | parser fixture (Ubuntu, RHEL) + `parser_version` |
| Celery 스케줄 드리프트 | Beat + DB에 next_run 기록 |
| DB 용량 | hypertable retention + rollup 위주 조회 |

---

## 10. 확인 체크리스트 (승인용)

- [ ] **옵션 A 스택** (FastAPI + Celery + PostgreSQL/TimescaleDB + Next.js) 확정
- [ ] **Phase 1 = 중앙 SSH Pull** 확정
- [ ] **asyncssh** 우선, Paramiko fallback 검토 수용
- [ ] **TimescaleDB** hypertable·rollup 전략 수용
- [ ] 기본 **폴링 60초**, 호스트 **~50대** 가정 (변경 가능)
- [ ] **Figma 대체** — design tokens + View/Container 분리 구조 수용

**승인자:** _______________  
**승인일:** _______________

---

## 11. 참고 자료

- [FastAPI](https://fastapi.tiangolo.com/)
- [Celery](https://docs.celeryq.dev/)
- [asyncssh](https://asyncssh.readthedocs.io/)
- [TimescaleDB](https://docs.timescale.com/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/)
- [react-calendar-heatmap](https://www.npmjs.com/package/react-calendar-heatmap)

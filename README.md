# SSH Remote Monitoring Tool

원격 Linux 호스트에 SSH로 접속하여 프로세스·세션을 수집하고, 시스템/사용자 프로세스를 분류한 뒤 웹 대시보드와 GitHub 스타일 활동 캘린더로 모니터링하는 도구입니다.

## 기술 스택 (옵션 A)

- **Backend:** FastAPI, Celery, Redis, SQLAlchemy, Alembic
- **SSH:** asyncssh
- **Database:** PostgreSQL + TimescaleDB
- **Frontend:** Next.js (App Router), Tailwind CSS, react-calendar-heatmap, Recharts
- **Deploy:** Docker Compose, GitHub Actions

## 문서 (승인 순서)

1. [research.md](./research.md) — 기술 조사·스택 결정
2. [plan.md](./plan.md) — 아키텍처·단계별 계획
3. [implement.md](./implement.md) — 구현 체크리스트

각 문서 하단의 **확인 체크리스트**에 승인한 뒤 다음 단계로 진행합니다.

## 현재 상태

- **옵션 A** (Python / FastAPI) 선택
- 설계 문서 초안 작성됨
- **Figma 대체용** `web/` UI 스캐폴드 (design tokens, ui primitives, View/Container 패턴)
- 코드 구현: `implement.md` 게이트 승인 후 착수

> 이전 옵션 B(NestJS) 설계는 브랜치 `cursor/option-b-docs-574a`에 보관되어 있습니다.

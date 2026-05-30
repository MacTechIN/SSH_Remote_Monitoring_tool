# SSH Remote Monitoring Tool

원격 Linux 호스트에 SSH로 접속하여 프로세스·세션을 수집하고, 시스템/사용자 프로세스를 분류한 뒤 웹 대시보드와 GitHub 스타일 활동 캘린더로 모니터링하는 도구입니다.

## 기술 스택 (옵션 B)

- **Backend:** NestJS, BullMQ, Redis, Prisma, PostgreSQL, Socket.io
- **Frontend:** Next.js (App Router), Tailwind CSS, Recharts / react-calendar-heatmap
- **Deploy:** Docker Compose, GitHub Actions

## 문서 (승인 순서)

1. [research.md](./research.md) — 기술 조사·스택 결정
2. [plan.md](./plan.md) — 아키텍처·단계별 계획
3. [implement.md](./implement.md) — 구현 체크리스트

각 문서 하단의 **확인 체크리스트**에 승인한 뒤 다음 단계로 진행합니다.

## 현재 상태

- 옵션 B 선택 완료
- 설계 문서 초안 작성됨
- 코드 구현: `implement.md` 게이트 승인 후 착수

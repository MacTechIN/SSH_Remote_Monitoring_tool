# Research — SSH 원격 프로세스 모니터링 (옵션 B)

> **상태:** 초안 · **선택 스택:** 옵션 B (Node.js 풀스택)  
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

## 2. 스택 결정 — 옵션 B

사용자가 **옵션 B**를 선택함. 아래 구성으로 일원화한다.

| 계층 | 기술 | 버전 가이드 (2026 기준) |
|------|------|-------------------------|
| API·비즈니스 | **NestJS** | v11.x |
| 언어 | **TypeScript** | 5.x |
| SSH 클라이언트 | **ssh2** (또는 `node-ssh` 래퍼) | 최신 안정 |
| 작업 스케줄·큐 | **BullMQ** + **Redis** | BullMQ 5.x |
| ORM | **Prisma** | 6.x |
| DB | **PostgreSQL** | 16+ |
| 실시간 | **Socket.io** (NestJS Gateway) | 4.x |
| 프론트엔드 | **Next.js** (App Router) | 15.x |
| UI·차트 | Tailwind CSS, **Recharts** / **react-calendar-heatmap** | — |
| 인증 (관리 UI) | JWT + HttpOnly Cookie (또는 NextAuth) | MVP 이후 확장 |
| 컨테이너 | Docker Compose (api, worker, redis, postgres, web) | — |
| CI/CD | **GitHub Actions** → 이미지 빌드·배포 | — |

### 옵션 B를 선택한 근거

1. **실시간 대시보드**: WebSocket과 NestJS Gateway가 자연스럽게 맞물림.
2. **단일 언어**: 프론트·백·워커 스크립트를 TypeScript로 통일해 유지보수 비용 감소.
3. **모듈 구조**: 호스트·자격증명·수집·집계·API를 Nest 모듈로 분리하기 좋음.
4. **큐 기반 폴링**: 호스트별 BullMQ Job으로 재시도·백오프·동시성 제어가 명확함.
5. **Git 배포**: Next.js 정적/SSR + Nest API를 모노레포(turborepo 또는 npm workspaces)로 묶기 용이.

---

## 3. 수집 아키텍처

### 3.1 권장 모델: 중앙 Pull (Phase 1)

```
┌─────────────┐     SSH      ┌──────────────────┐
│ Nest Worker │ ──────────► │ Remote Linux Host │
│ (BullMQ)    │   ps/who/w   │                  │
└──────┬──────┘              └──────────────────┘
       │ INSERT snapshot
       ▼
┌─────────────┐     WS       ┌─────────────┐
│ PostgreSQL  │ ◄─────────── │ Nest API    │ ◄── Next.js
└─────────────┘              └─────────────┘
```

- **에이전트 설치 없이** 시작: 중앙 서버가 등록된 호스트에 주기적으로 SSH 접속.
- Phase 2에서 필요 시 경량 **Push 에이전트**(동일 스택의 작은 Node/Go 바이너리) 검토 가능.

### 3.2 SSH에서 실행할 명령 (초기 세트)

| 명령 | 용도 |
|------|------|
| `ps -eo pid,ppid,user:32,comm,cmd,%cpu,%mem,etime --sort=-%cpu` | 프로세스 목록 |
| `who -u` / `w -h` | 로그인 세션·idle 시간 |
| `id -u <user>` (필요 시) | UID 확인 |
| `systemctl show -p MainPID ...` (선택) | systemd 연동 분류 강화 |

출력은 **파서 모듈**에서 정규화한 뒤 JSON 스키마로 DB에 저장.

### 3.3 프로세스 분류 규칙 (초안)

| 분류 | 조건 예시 |
|------|-----------|
| `system` | UID 0 이고 allowlist에 포함 (sshd, systemd, cron, …) |
| `system` | PPID가 1(systemd)이고 comm이 커널/데몬 allowlist |
| `user` | 로그인 사용자 UID ≥ 1000 (또는 설정 가능 min_uid) |
| `user` | 해당 사용자의 TTY/세션과 연관된 프로세스 트리 |
| `unknown` | 규칙 미매칭 — 수동 태깅·규칙 학습 후보 |

규칙은 DB 테이블 `classification_rules`로 관리해 코드 배포 없이 조정 가능하게 한다.

### 3.4 보안

- SSH **개인키**만 사용 (비밀번호 인증 비권장).
- 키·호스트 비밀번호는 DB **암호화 at rest** (AES-256-GCM, `ENCRYPTION_KEY` 환경 변수).
- API는 관리자 인증 필수; 수집 워커는 내부 네트워크 전용.
- SSH `known_hosts` 검증 필수 (MITM 방지).
- 감사 로그: 누가 호스트를 등록/삭제했는지 `audit_events` 테이블.

---

## 4. 데이터 모델 (개념)

### 4.1 핵심 엔티티

- **Host** — hostname, port, ssh_user, encrypted_private_key, poll_interval_sec, enabled
- **ProcessSnapshot** — host_id, collected_at, raw_json (JSONB), parser_version
- **ProcessRecord** — snapshot_id, pid, ppid, user, comm, cmd, cpu, mem, classification, duration_estimate
- **UserSession** — snapshot_id, user, tty, login_at, idle, from_ip
- **DailyActivityRollup** — host_id, user, date, hour (0–23), event_count, total_cpu_sec, top_processes (JSONB) — heatmap·tooltip용
- **AuditEvent** — actor, action, target, created_at

### 4.2 인덱스·성능

- `(host_id, collected_at DESC)` — 최신 스냅샷·타임라인
- `(host_id, user, date)` on `DailyActivityRollup` — 캘린더 API
- 오래된 `ProcessSnapshot.raw_json`은 90일 후 아카이브(선택) — Phase 2

---

## 5. API·실시간 설계 (요약)

| 용도 | 방식 |
|------|------|
| 호스트 CRUD, 규칙, 검색 | REST `/api/v1/...` |
| 라이브 “지금 상태” | WS `snapshot:update`, `session:update` |
| 캘린더 heatmap | REST `GET /api/v1/activity/calendar?from=&to=&granularity=day\|week\|month\|year` |
| 날짜 hover | REST `GET /api/v1/activity/day-summary?date=&host_id=` (rollup 캐시) |

---

## 6. 프론트엔드 UI 조사

### 6.1 Heatmap (GitHub 스타일)

- **react-calendar-heatmap**: GitHub과 유사한 주 단위 그리드, `title`/`transformDayElement`로 tooltip.
- **Recharts**: 일·시간 2단계 drill-down(24시간 막대)에 적합.
- 색 단계: 활동량(스냅샷 수 또는 CPU·초 합)을 quantile로 4~5단계 녹색 계열.

### 6.2 화면 목록 (MVP)

1. **대시보드** — 호스트별 현재 사용자·프로세스 테이블 (WS)
2. **호스트 관리** — 등록·연결 테스트·폴링 주기
3. **활동 캘린더** — 년/월/주/일 전환 + hover tooltip
4. **검색** — 사용자·명령어·기간 필터
5. **설정** — 분류 규칙 (관리자)

---

## 7. BullMQ 작업 설계

| Queue | Job | 설명 |
|-------|-----|------|
| `host-poll` | `PollHostJob` | 단일 호스트 SSH 수집 |
| `rollup` | `BuildDailyRollupJob` | 스냅샷 → 시간대별 집계 |
| `schedule` | repeatable | 호스트별 `poll_interval`마다 `PollHostJob` enqueue |

- 동시 SSH 연결 상한: `SSH_CONCURRENCY=10` (환경 변수).
- 실패 시 exponential backoff, 3회 후 `dead-letter` + 알림(Phase 2).

---

## 8. 대안·리스크

| 리스크 | 완화 |
|--------|------|
| SSH 연결 폭주 | BullMQ concurrency + 호스트별 간격 |
| `ps` 출력 OS별 차이 | parser_version + 통합 테스트 fixture (Ubuntu, RHEL) |
| DB 용량 증가 | rollup 위주 조회, raw JSON TTL |
| 키 유출 | 암호화 + 시크릿은 Git에 미포함 |
| 실시간 부하 | 스냅샷 diff만 WS 전송 |

---

## 9. 모노레포 구조 (권장)

```
/
├── apps/
│   ├── api/          # NestJS (API + WS)
│   ├── worker/       # NestJS standalone 또는 동일 앱의 worker 프로세스
│   └── web/          # Next.js
├── packages/
│   └── shared/       # DTO, 타입, 분류 규칙 상수
├── prisma/
├── docker-compose.yml
└── .github/workflows/
```

---

## 10. 확인 체크리스트 (승인용)

다음 항목에 동의하면 `plan.md` 작성·세부 일정 확정으로 진행한다.

- [ ] **옵션 B 스택** (NestJS + BullMQ + PostgreSQL + Next.js + Socket.io) 확정
- [ ] **Phase 1 = 중앙 SSH Pull** (에이전트 없음) 확정
- [ ] **프로세스 분류 규칙** 초안(UID/allowlist/세션 연관) 수용
- [ ] **모노레포** 구조 수용
- [ ] (선택) 예상 호스트 수·폴링 주기: 기본 **60초**, 호스트 **~50대** 가정 — 변경 시 plan에 반영

**승인자:** _______________  
**승인일:** _______________

---

## 11. 참고 자료

- [NestJS Documentation](https://docs.nestjs.com/)
- [BullMQ — Patterns](https://docs.bullmq.io/)
- [Prisma — PostgreSQL JSON](https://www.prisma.io/docs/orm/prisma-client/special-fields-and-types/working-with-json-fields)
- [ssh2 npm](https://www.npmjs.com/package/ssh2)
- [react-calendar-heatmap](https://www.npmjs.com/package/react-calendar-heatmap)

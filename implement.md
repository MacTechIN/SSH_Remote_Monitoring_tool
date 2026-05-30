# Implement — SSH 원격 프로세스 모니터링 (옵션 B)

> **전제:** `research.md`, `plan.md` 승인  
> **상태:** 구현 대기 · **용도:** 단계별 구현·검증 체크리스트

구현 시 이 문서의 체크박스를 순서대로 완료하고, 각 **게이트**에서 확인을 받은 뒤 다음 섹션으로 진행한다.

---

## 게이트 0 — 문서 승인

- [ ] `research.md` 검토 완료
- [ ] `plan.md` 검토 완료
- [ ] 본 `implement.md` 착수 승인

---

## 1. 저장소 초기화

### 1.1 모노레포

- [ ] 루트 `package.json` — workspaces: `apps/*`, `packages/*`
- [ ] `packages/shared` — 공유 타입·상수 (`ProcessClass`, DTO)
- [ ] `apps/api` — NestJS CLI 생성
- [ ] `apps/worker` — NestJS worker (또는 api의 `worker` entry)
- [ ] `apps/web` — `create-next-app` App Router + Tailwind
- [ ] 루트 스크립트: `dev`, `build`, `lint`, `test`

### 1.2 품질 도구

- [ ] ESLint + Prettier (공유 config)
- [ ] TypeScript `strict: true`
- [ ] Husky + lint-staged (선택)

**게이트 1 확인:** 로컬에서 `npm install` 성공

---

## 2. 인프라

### 2.1 Docker Compose

- [ ] `postgres:16`, `redis:7` 서비스
- [ ] `api`, `worker`, `web` 빌드·의존성 순서
- [ ] 볼륨·헬스체크

### 2.2 Prisma

- [ ] `schema.prisma` — Host, ProcessSnapshot, ProcessRecord, UserSession, DailyActivityRollup, ClassificationRule, AuditEvent
- [ ] 초기 마이그레이션 `npx prisma migrate dev`
- [ ] 시드: 기본 system allowlist 규칙

### 2.3 환경

- [ ] `.env.example` 문서화
- [ ] `ENCRYPTION_KEY` 생성 방법 README에 기재

**게이트 2 확인:** `docker compose up` 후 postgres/redis healthy

---

## 3. 백엔드 — SSH·수집

### 3.1 SSH 모듈

- [ ] `SshService.connect(host)` — ssh2 + known_hosts
- [ ] `exec(command)` — 타임아웃 30s
- [ ] 연결 종료·에러 매핑

### 3.2 파서

- [ ] `parsePs(output)` → `ProcessDto[]`
- [ ] `parseWho(output)` → `SessionDto[]`
- [ ] Fixture 테스트 2종 이상 OS 샘플

### 3.3 분류

- [ ] `ClassificationService.classify(process, sessions, rules)`
- [ ] DB 규칙 로드 + allowlist 시드

### 3.4 수집기

- [ ] `CollectorService.collect(hostId)` — SSH → parse → classify → transaction save
- [ ] `EventsGateway.emitSnapshot(hostId, summary)`

**게이트 3 확인:** 수동 스크립트로 1호스트 수집 후 DB row 확인

---

## 4. 백엔드 — 큐·스케줄

- [ ] BullMQ 연결 모듈
- [ ] `PollHostProcessor` — `CollectorService` 호출
- [ ] Host create/update 시 repeatable job 등록
- [ ] Host disable 시 job 제거
- [ ] `BuildDailyRollupProcessor` — cron 또는 poll 후 chain
- [ ] `SSH_CONCURRENCY` limiter

**게이트 4 확인:** 2분간 자동 폴링·rollup row 생성

---

## 5. 백엔드 — REST·Auth

- [ ] `HostController` — CRUD + test-connection
- [ ] `ActivityController` — calendar, day-summary
- [ ] `SearchController` — processes 검색
- [ ] `AuthModule` — JWT login (단일 admin MVP)
- [ ] ValidationPipe + DTO (class-validator)

**게이트 5 확인:** Postman/curl로 API 계약 검증

---

## 6. 프론트엔드

### 6.1 공통

- [ ] API base URL env
- [ ] React Query 또는 SWR
- [ ] Socket.io client hook

### 6.2 페이지

- [ ] `/` 대시보드 — 라이브 테이블
- [ ] `/activity` — heatmap + granularity 토글
- [ ] `/activity` — DayTooltip 컴포넌트 (day-summary API)
- [ ] `/activity/[date]` — 24h Recharts
- [ ] `/hosts` — CRUD + test
- [ ] `/search` — 필터 폼 + 결과 테이블

### 6.3 UI

- [ ] system/user 뱃지 색상
- [ ] 반응형 레이아웃 (최소 desktop-first)

**게이트 6 확인:** 브라우저에서 WS 갱신·캘린더 hover 동작

---

## 7. CI/CD

- [ ] `.github/workflows/ci.yml` — install, lint, test, prisma validate
- [ ] Docker build job (main push)
- [ ] README: 배포 절차

**게이트 7 확인:** CI green on PR

---

## 8. 보안·운영 체크 (출시 전)

- [ ] SSH 키·JWT·ENCRYPTION_KEY가 Git에 없음
- [ ] CORS production origin 설정
- [ ] Rate limit (선택 `@nestjs/throttler`)
- [ ] 로그에 cmd 전체 마스킹 옵션 (선택)

---

## 9. 완료 정의 (Definition of Done)

MVP 완료로 간주하려면 다음이 모두 참이어야 한다.

1. 등록한 호스트에서 **60초 주기**로 스냅샷이 쌓인다.
2. 대시보드에서 **실시간**으로 사용자·프로세스가 보인다.
3. 활동 페이지에서 **일/주/월/년** heatmap이 보이고, **hover 시 해당일 요약**이 표시된다.
4. 검색으로 **과거 기간·사용자·명령** 필터가 동작한다.
5. `docker compose up` 및 **GitHub Actions**로 빌드가 통과한다.

---

## 10. 구현 순서 요약 (한 줄)

```
모노레포 → Docker/Prisma → SSH/Parser/Collector → BullMQ → REST/WS → Next UI → CI
```

---

## 11. 승인·진행 로그

| 날짜 | 단계 | 확인자 | 비고 |
|------|------|--------|------|
| | 게이트 0 | | |
| | 게이트 1–7 | | |
| | MVP DoD | | |

---

**다음 액션:** 게이트 0–2 승인 시 → `implement.md` §1–2 코드 작성(모노레포·Docker·Prisma) 착수.

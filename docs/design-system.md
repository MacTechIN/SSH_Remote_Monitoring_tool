# Design System — Figma 디자인 대체 가이드

추후 Figma에서 완성된 UI로 **스타일·레이아웃만 교체**하고, 데이터·비즈니스 로직은 그대로 유지하기 위한 규칙입니다.

---

## 1. 레이어 분리 (필수)

```
┌─────────────────────────────────────────┐
│  Page (app/**/page.tsx)                 │  ← 라우팅·데이터 fetch만
├─────────────────────────────────────────┤
│  Feature Container (features/*)         │  ← hooks, API, WS, 상태
├─────────────────────────────────────────┤
│  Feature View (features/*/ *View.tsx)   │  ← props만 받는 Presentational
├─────────────────────────────────────────┤
│  UI Primitives (components/ui/*)        │  ← Figma 컴포넌트와 1:1 매핑
├─────────────────────────────────────────┤
│  Design Tokens (design-tokens/*)        │  ← Figma Variables → CSS 변수
└─────────────────────────────────────────┘
```

| 레이어 | Figma 교체 시 | 변경 금지 |
|--------|---------------|-----------|
| `page.tsx` | import 경로만 | fetch·라우트 파라미터 |
| `*Container.tsx` | 없음 | hooks, API 호출 |
| `*View.tsx` | **마크업·className 전면 교체** | props 타입·이름 |
| `components/ui/*` | **Figma 컴포넌트로 교체** | public props (variant, size) |
| `design-tokens/*` | **tokens.json / tokens.css 갱신** | 토큰 키 이름 (semver) |

---

## 2. Figma → 코드 워크플로

1. Figma **Variables** (색, 간격, radius, typography)보내기 또는 Dev Mode 스펙 확인
2. `web/src/design-tokens/figma-map.json`에 Figma 변수명 ↔ CSS 변수명 매핑
3. `tokens.json` / `tokens.css` 갱신 (스크립트 `npm run tokens:sync` — 구현 시)
4. `components/ui/*`를 Figma 컴포넌트 구조에 맞게 교체
5. `*View.tsx`에서 레이아웃·간격만 조정 (데이터 바인딩은 Container 유지)
6. (선택) **Figma Code Connect** — `web/figma/code-connect/*.figma.tsx`

---

## 3. 디자인 토큰 규칙

- 모든 색·간격·폰트는 **하드코딩 금지** → `var(--token-*)` 또는 Tailwind `theme.extend`가 tokens 참조
- Heatmap 활동 색: `--activity-0` … `--activity-4` (Figma 녹색 스케일과 동기화)
- 다크 모드: `[data-theme="dark"]` 루트에서 동일 키 재정의

토큰 키는 **breaking change 시에만** 변경. 값만 바꾸면 Figma 리디자인 전체 반영 가능.

---

## 4. 화면별 Figma 컴포넌트 매핑 (예정)

| 화면 | View 파일 | Figma Frame (예시 이름) |
|------|-----------|-------------------------|
| 대시보드 | `DashboardView.tsx` | `Dashboard / Default` |
| 활동 캘린더 | `ActivityHeatmapView.tsx` | `Activity / Calendar` |
| 호스트 목록 | `HostsView.tsx` | `Hosts / List` |
| 검색 | `SearchView.tsx` | `Search / Results` |
| 공통 | `AppShell.tsx` | `Layout / App Shell` |

Figma 파일 URL·file key는 `web/figma/README.md`에 기록.

---

## 5. Tailwind 연동

`tailwind.config.ts`는 `tokens.css`의 CSS 변수를 `theme.extend.colors`, `spacing`, `borderRadius`에 매핑.
Figma 교체 후 **config 수정 최소화** — tokens.css만 갱신하는 것이 목표.

---

## 6. 차트·Heatmap

- **Recharts / react-calendar-heatmap**: 색은 `getActivityColor(level)` → 내부적으로 design token 사용
- Figma에서 차트 스타일이 바뀌면 `ActivityHeatmapView`의 `className`·`colorScale` props만 변경

---

## 7. 검증 체크리스트 (Figma 반영 후)

- [ ] `tokens.css`가 Figma Variables와 일치
- [ ] UI primitives에 하드코딩 hex 없음
- [ ] Container 파일 diff 없음 (로직 무변경)
- [ ] Storybook 또는 `/design-preview` (선택)에서 토큰·컴포넌트 시각 회귀
- [ ] a11y: contrast WCAG AA (Figma 플러그인 또는 axe)

---

## 8. 관련 경로

| 경로 | 용도 |
|------|------|
| `web/src/design-tokens/` | 토큰 소스 |
| `web/src/components/ui/` | Figma 1:1 primitives |
| `web/src/components/features/` | Container + View |
| `web/figma/code-connect/` | Code Connect 템플릿 |
| `web/DESIGN_HANDOFF.md` | 파일별 체크리스트 |

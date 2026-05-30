# Web (Next.js) — Figma 대체 준비 구조

Next.js 앱 구현 전 **디자인 교체용 스캐폴드**입니다.

## 디렉터리

| 경로 | 역할 |
|------|------|
| `src/design-tokens/` | Figma Variables → CSS/JSON |
| `src/components/ui/` | Figma 1:1 primitives (`Button`, `Badge`, …) |
| `src/components/layouts/` | `AppShell` 등 레이아웃 |
| `src/components/features/*/` | `*View` (UI) + `*Container` (로직) |
| `figma/code-connect/` | Code Connect 예시 |
| `scripts/sync-tokens-from-figma.mjs` | 토큰 동기화 스켈레톤 |

## Figma 반영

1. [DESIGN_HANDOFF.md](./DESIGN_HANDOFF.md)에 파일 URL 기입
2. Variables export → `npm run tokens:sync` (package.json 추가 후)
3. `components/ui`, `*View.tsx` 스타일 교체

상세: [../docs/design-system.md](../docs/design-system.md)

## Next.js 연동 시

```ts
// app/globals.css
@import "../src/design-tokens/tokens.css";
@import "../src/components/ui/ui-primitives.css";
@import "../src/components/layouts/app-shell.css";
@import "../src/components/features/ActivityHeatmap/activity-heatmap.css";
```

`tsconfig paths`: `"@/*": ["./src/*"]`

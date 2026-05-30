# Figma Design Handoff

## Figma 파일 (추후 기입)

| 항목 | 값 |
|------|-----|
| File name | _TBD_ |
| File URL | _TBD_ |
| File key | _TBD_ |
| Library (Design System) | _TBD_ |

## 교체 순서

1. `src/design-tokens/tokens.json` + `tokens.css` 업데이트
2. `src/design-tokens/figma-map.json` — Figma Variable 이름 동기화
3. `src/components/ui/*` — Figma Component와 1:1 교체
4. `src/components/features/**/*View.tsx` — 레이아웃·스타일만
5. `figma/code-connect/*.figma.tsx` — Code Connect (선택)

## 스크립트 (구현 Phase에서 추가)

```bash
# Figma Variables JSON → tokens (예시)
npm run tokens:sync -- ./figma/export/variables.json
```

## 주의

- `*Container.tsx`, `src/hooks/*`, `src/lib/api/*`는 Figma 작업 범위 **외**
- 페이지 `page.tsx`는 View + Container 조합만 유지

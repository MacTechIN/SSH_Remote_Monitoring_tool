/**
 * Design tokens — programmatic access for charts & JS logic.
 * 시각 스타일은 tokens.css; 차트 색상 등은 여기서 CSS 변수 읽기.
 */
import tokensJson from "./tokens.json";

export type ActivityLevel = 0 | 1 | 2 | 3 | 4;

export const tokens = tokensJson;

/** 브라우저에서 computed style로 activity 색 반환 (Figma 교체 후 자동 반영) */
export function getActivityColor(level: ActivityLevel): string {
  if (typeof document === "undefined") {
    const key = String(level) as keyof typeof tokens.activity;
    return tokens.activity[key]?.value ?? tokens.activity["0"].value;
  }
  const root = document.documentElement;
  return getComputedStyle(root).getPropertyValue(`--activity-${level}`).trim() || "#161b22";
}

export function getCssVar(name: string): string {
  if (typeof document === "undefined") return "";
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

/** classification 뱃지 — Figma badge 컴포넌트 색과 동기화 */
export const classificationTokenVar = {
  system: "--color-badge-system",
  user: "--color-badge-user",
  unknown: "--color-badge-unknown",
} as const;

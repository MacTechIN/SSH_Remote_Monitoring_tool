/**
 * className 병합 — Figma 교체 시 variant class만 ui 컴포넌트 내부에서 관리.
 */
type ClassValue = string | undefined | null | false;

export function cn(...classes: ClassValue[]): string {
  return classes.filter(Boolean).join(" ");
}

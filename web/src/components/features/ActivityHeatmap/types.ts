import type { ReactNode } from "react";

/** API → View 전용 DTO. Figma 교체와 무관하게 안정적으로 유지 */

export type ActivityGranularity = "day" | "week" | "month" | "year";

export interface CalendarCell {
  date: string;
  /** 0–4, design token activity level */
  level: 0 | 1 | 2 | 3 | 4;
  count: number;
}

export interface DaySummaryLine {
  user: string;
  summary: string;
}

export interface ActivityHeatmapViewProps {
  granularity: ActivityGranularity;
  cells: CalendarCell[];
  loading?: boolean;
  /** hover tooltip — Figma Tooltip 컴포넌트로 교체 가능 */
  onCellHover?: (date: string, anchor: HTMLElement) => void;
  onCellClick?: (date: string) => void;
  onGranularityChange?: (g: ActivityGranularity) => void;
  /** Figma에서 제공 시 slot */
  toolbarSlot?: ReactNode;
}

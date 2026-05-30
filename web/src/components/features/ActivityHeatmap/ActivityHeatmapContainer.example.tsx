/**
 * EXAMPLE — 구현 시 ActivityHeatmapContainer.tsx로 복사.
 * Figma 교체 대상 아님: API·상태만 담당.
 */
"use client";

import { useCallback, useState } from "react";
import { ActivityHeatmapView } from "./ActivityHeatmapView";
import type { ActivityGranularity, CalendarCell } from "./types";

export function ActivityHeatmapContainerExample() {
  const [granularity, setGranularity] = useState<ActivityGranularity>("day");
  const [cells] = useState<CalendarCell[]>([]);

  const onCellHover = useCallback((date: string) => {
    // fetch GET /api/v1/activity/day-summary?date=
    void date;
  }, []);

  return (
    <ActivityHeatmapView
      granularity={granularity}
      cells={cells}
      onGranularityChange={setGranularity}
      onCellHover={onCellHover}
      onCellClick={(date) => {
        window.location.href = `/activity/${date}`;
      }}
    />
  );
}

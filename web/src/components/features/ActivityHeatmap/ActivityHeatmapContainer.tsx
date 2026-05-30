"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { ActivityHeatmapView } from "./ActivityHeatmapView";
import type { ActivityGranularity, CalendarCell } from "./types";

function defaultRange() {
  const to = new Date();
  const from = new Date();
  from.setDate(from.getDate() - 90);
  return { from: from.toISOString().slice(0, 10), to: to.toISOString().slice(0, 10) };
}

export function ActivityHeatmapContainer({ hostId }: { hostId?: string }) {
  const [granularity, setGranularity] = useState<ActivityGranularity>("day");
  const [cells, setCells] = useState<CalendarCell[]>([]);
  const [loading, setLoading] = useState(true);
  const [tooltip, setTooltip] = useState<string>("");

  const load = useCallback(async () => {
    setLoading(true);
    const { from, to } = defaultRange();
    try {
      const data = await api.activity.calendar(from, to, hostId);
      setCells(
        data.cells.map((c) => ({
          date: c.date,
          level: c.level as CalendarCell["level"],
          count: c.count,
        })),
      );
    } catch {
      setCells([]);
    } finally {
      setLoading(false);
    }
  }, [hostId]);

  useEffect(() => {
    load();
  }, [load]);

  const onCellHover = useCallback(
    async (date: string) => {
      try {
        const summary = await api.activity.daySummary(date, hostId);
        const text = summary.lines.map((l) => `${l.user}: ${l.summary}`).join(" | ");
        setTooltip(text || "활동 없음");
      } catch {
        setTooltip("");
      }
    },
    [hostId],
  );

  return (
    <div>
      <h1 style={{ fontSize: "var(--font-size-xl)" }}>활동 캘린더</h1>
      {tooltip && (
        <p
          style={{
            fontSize: "var(--font-size-sm)",
            color: "var(--color-text-secondary)",
            minHeight: "1.5em",
          }}
          role="status"
        >
          {tooltip}
        </p>
      )}
      <ActivityHeatmapView
        granularity={granularity}
        cells={cells}
        loading={loading}
        onGranularityChange={setGranularity}
        onCellHover={(date) => onCellHover(date)}
        onCellClick={(date) => {
          window.location.href = `/activity/${date}`;
        }}
      />
    </div>
  );
}

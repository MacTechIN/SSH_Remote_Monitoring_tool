import { getActivityColor } from "@/design-tokens";
import { cn } from "@/lib/cn";
import type { CSSProperties } from "react";
import type { ActivityGranularity, ActivityHeatmapViewProps, CalendarCell } from "./types";

const GRANULARITIES: ActivityGranularity[] = ["day", "week", "month", "year"];

function cellStyle(level: CalendarCell["level"]): CSSProperties {
  return { backgroundColor: getActivityColor(level) };
}

/**
 * Presentational only — Figma `Activity / Calendar` 프레임으로 교체.
 * 데이터·이벤트는 props; fetch/WS는 ActivityHeatmapContainer에서 처리.
 */
export function ActivityHeatmapView({
  granularity,
  cells,
  loading,
  onCellHover,
  onCellClick,
  onGranularityChange,
  toolbarSlot,
}: ActivityHeatmapViewProps) {
  return (
    <section className="activity-heatmap" data-figma-component="Activity/Calendar">
      <div className="activity-heatmap__toolbar">
        {toolbarSlot ?? (
          <div className="activity-heatmap__granularity" role="tablist">
            {GRANULARITIES.map((g) => (
              <button
                key={g}
                type="button"
                role="tab"
                aria-selected={granularity === g}
                className={cn("activity-heatmap__tab", granularity === g && "activity-heatmap__tab--active")}
                onClick={() => onGranularityChange?.(g)}
              >
                {g}
              </button>
            ))}
          </div>
        )}
      </div>

      {loading ? (
        <p className="activity-heatmap__loading" style={{ color: "var(--color-text-secondary)" }}>
          Loading…
        </p>
      ) : (
        <div className="activity-heatmap__grid" role="grid" aria-label="Activity calendar">
          {cells.map((cell) => (
            <button
              key={cell.date}
              type="button"
              className="activity-heatmap__cell"
              style={cellStyle(cell.level)}
              title={`${cell.date}: ${cell.count}`}
              onMouseEnter={(e) => onCellHover?.(cell.date, e.currentTarget)}
              onClick={() => onCellClick?.(cell.date)}
            />
          ))}
        </div>
      )}
    </section>
  );
}
